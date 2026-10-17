from datetime import datetime, date, time
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_pending, delete, update
from src.schedule.overdue import refresh_overdue
from src.schedule.tags import fetch_tags
from src.schedule.categories import fetch_categories
from src.time_utils import today_bj

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("📋 待完成日程")

all_tags = fetch_tags(user.id)
all_cats = fetch_categories(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}
cat_names = [c["name"] for c in all_cats]

# 标签筛选放入一个折叠框里，界面更干净
with st.expander("🔍 筛选选项", expanded=False):
    filter_ids = []
    if all_tags:
        groups = {}
        for t in all_tags:
            groups.setdefault(t["group_name"], []).append(t)
        cols = st.columns(len(groups))
        for i, (group_name, items) in enumerate(groups.items()):
            with cols[i % len(groups)]:
                chosen = st.multiselect(
                    f"按{group_name}",
                    options=[t["id"] for t in items],
                    format_func=lambda tid: next(
                        t["name"] for t in items if t["id"] == tid
                    ),
                    key=f"filter_{group_name}",
                )
                filter_ids.extend(chosen)

pending = fetch_pending(user.id)
if filter_ids:
    pending = [s for s in pending if set(s["tag_ids"]) & set(filter_ids)]

if not pending:
    st.success("暂无待完成日程 🎉")
    st.stop()

# 渲染待完成列表
for s in pending:
    with st.container(border=True):
        # ========== 第一行：信息 + 标签 + 按钮 ==========
        # 重新分配列宽：给按钮列留出足够空间，保证文字不被挤压
        c_cat, c_note, c_tags, c_date, c_edit, c_done, c_del = st.columns([2, 3.5, 2.5, 1.5, 1.2, 1.2, 1.2])
        
        with c_cat:
            st.markdown(f"<div style='font-weight: 600; font-size: 1.05em; line-height: 2.3;'>{s['category']}</div>", unsafe_allow_html=True)
            
        with c_note:
            note_text = s['note'] or '（无备注）'
            st.markdown(f"<div style='color: #475569; line-height: 2.3;'>{note_text}</div>", unsafe_allow_html=True)
            
        with c_tags:
            if s["tag_ids"]:
                tags_html = ""
                for tid in s["tag_ids"]:
                    if tid in tag_map:
                        tags_html += f"<span style='background-color:#EFF6FF; color:#2563EB; padding:2px 8px; border-radius:9999px; font-size:0.75rem; margin-right:4px; display:inline-block; margin-top:6px;'>{tag_map[tid]}</span>"
                st.markdown(tags_html, unsafe_allow_html=True)
                
        with c_date:
            date_str = datetime.fromisoformat(s['deadline_date']).strftime("%m-%d")
            date_html = f"<div style='color: #94A3B8; font-size: 0.9em; line-height: 2.3; text-align: right; margin-right: 8px;'>截止: {date_str}"
            if s["status"] == "overdue":
                date_html += f"<br><span style='color:#EF4444; font-weight:500;'>逾期 {s['overdue_days']} 天</span>"
            date_html += "</div>"
            st.markdown(date_html, unsafe_allow_html=True)
            
        with c_edit:
            edit_key = f"toggle_edit_{s['id']}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
                
            if st.button("编辑", key=f"btn_edit_{s['id']}", use_container_width=True):
                st.session_state[edit_key] = not st.session_state[edit_key]
                st.rerun()
                
        with c_done:
            # 注入专属的绿色按钮 CSS（完全覆盖 primary 的默认大红底色，并保证边框一致）
            st.markdown("""
            <style>
            /* 绿色按钮 */
            div[data-testid="stButton"] > button.green-btn {
                background-color: #10B981 !important;
                color: white !important;
                border: 1px solid #10B981 !important;
                box-shadow: none !important;
            }
            div[data-testid="stButton"] > button.green-btn:hover {
                background-color: #059669 !important;
                border-color: #059669 !important;
            }
            /* 保存修改按钮 */
            div[data-testid="stFormSubmitButton"] > button {
                background-color: #3B82F6 !important;
                color: white !important;
                border: 1px solid #3B82F6 !important;
            }
            div[data-testid="stFormSubmitButton"] > button:hover {
                background-color: #2563EB !important;
                border-color: #2563EB !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 这里不用 type="primary"，直接用普通按钮，靠 CSS 加绿
            if st.button("完成", key=f"done_{s['id']}", use_container_width=True, type="secondary"):
                update(s["id"], user.id, {"status": "completed"})
                st.rerun()
                
        with c_del:
            if st.button("删除", key=f"del_{s['id']}", use_container_width=True):
                delete(s["id"], user.id)
                st.rerun()

        # ========== 第二行（仅点击编辑时出现）：展开的编辑表单 ==========
        if st.session_state[edit_key]:
            st.divider()
            
            is_stage = bool(s.get("start_time") and s.get("end_time"))
            current_type = "阶段型" if is_stage else "ddl型"

            edit_type = st.radio(
                "日程类型", ["ddl型", "阶段型"],
                index=0 if current_type == "ddl型" else 1,
                horizontal=True, key=f"edit_type_{s['id']}"
            )

            deadline_val = datetime.fromisoformat(s["deadline_date"]).date()
            start_val = datetime.fromisoformat(s["start_time"]).time() if s.get("start_time") else time(11, 0)
            end_val = datetime.fromisoformat(s["end_time"]).time() if s.get("end_time") else time(13, 0)
            prep_val = datetime.fromisoformat(s["prep_start"]).date() if s.get("prep_start") else None
            cat_index = cat_names.index(s["category"]) if s["category"] in cat_names else 0

            with st.form(f"edit_{s['id']}_{edit_type}"):
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    new_cat = st.selectbox("类别", cat_names, index=cat_index)
                    new_note = st.text_input("备注", value=s["note"] or "")
                    new_dl = st.date_input("截止日期", value=deadline_val)
                with f_col2:
                    if edit_type == "阶段型":
                        new_start = st.time_input("开始时间", value=start_val)
                        new_end = st.time_input("结束时间", value=end_val)
                    else:
                        new_start, new_end = None, None
                    
                    new_prep = st.date_input("开始准备日期（可选）", value=prep_val if prep_val else today_bj())
                    new_tags = st.multiselect("标签", options=list(tag_map.keys()), default=s["tag_ids"], format_func=lambda tid: tag_map[tid])
                
                # 去掉 type="primary"，直接靠 CSS 变色
                saved = st.form_submit_button("保存修改")

            if saved:
                if edit_type == "阶段型" and new_end <= new_start:
                    st.error("结束时间必须晚于开始时间")
                else:
                    updates = {
                        "category": new_cat, "note": new_note,
                        "deadline_date": str(new_dl), "prep_start": str(new_prep) if new_prep else None,
                    }
                    if edit_type == "阶段型":
                        updates["start_time"] = datetime.combine(new_dl, new_start).isoformat()
                        updates["end_time"] = datetime.combine(new_dl, new_end).isoformat()
                    else:
                        updates["start_time"] = None
                        updates["end_time"] = None
                    update(s["id"], user.id, updates, tag_ids=new_tags)
                    st.success("已保存")
                    st.session_state[edit_key] = False
                    st.rerun()
