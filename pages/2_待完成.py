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

# 标签筛选
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

# ========== 自定义 CSS：让表单控件更紧凑 ==========
st.markdown("""
<style>
    /* 缩小表单项之间的垂直间距 */
    div[data-testid="stForm"] {
        padding: 1rem !important;
        border: none !important;
        background-color: transparent !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

# 渲染待完成列表
for s in pending:
    with st.container(border=True):
        # ========== 第一行：信息 + 按钮 ==========
        # 列宽分配：类别(2) + 备注(4) + 日期(2) + 编辑(1) + 完成(1) + 删除(1)
        c_cat, c_note, c_date, c_edit, c_done, c_del = st.columns([2, 4, 2, 1, 1, 1])
        
        with c_cat:
            st.markdown(f"<div style='font-weight: 600; font-size: 1.05em; line-height: 2.3;'>{s['category']}</div>", unsafe_allow_html=True)
            
        with c_note:
            note_text = s['note'] or '（无备注）'
            # 标签作为小字加在备注后面
            tags_html = ""
            if s["tag_ids"]:
                for tid in s["tag_ids"]:
                    if tid in tag_map:
                        tags_html += f"<span style='color:#2563EB; font-size:0.8em; margin-left:8px;'>#{tag_map[tid]}</span>"
            
            st.markdown(f"<div style='line-height: 2.3;'>{note_text}{tags_html}</div>", unsafe_allow_html=True)
            
        with c_date:
            date_str = datetime.fromisoformat(s['deadline_date']).strftime("%m-%d")
            date_html = f"<div style='color: #94A3B8; font-size: 0.9em; line-height: 2.3;'>截止: {date_str}"
            if s["status"] == "overdue":
                date_html += f" <span style='color:#EF4444; font-weight:500;'>· 逾期 {s['overdue_days']} 天</span>"
            date_html += "</div>"
            st.markdown(date_html, unsafe_allow_html=True)
            
        # 编辑按钮的状态控制
        edit_key = f"toggle_edit_{s['id']}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False
            
        with c_edit:
            btn_label = "收起" if st.session_state[edit_key] else "编辑"
            if st.button(btn_label, key=f"btn_edit_{s['id']}", use_container_width=True):
                st.session_state[edit_key] = not st.session_state[edit_key]
                st.rerun()
                
        with c_done:
            if st.button("完成", key=f"done_{s['id']}", use_container_width=True):
                update(s["id"], user.id, {"status": "completed"})
                st.rerun()
                
        with c_del:
            if st.button("删除", key=f"del_{s['id']}", use_container_width=True):
                delete(s["id"], user.id)
                st.rerun()

        # ========== 第二行：展开的编辑表单（极其紧凑） ==========
        if st.session_state[edit_key]:
            st.markdown("<hr style='margin: 0.5rem 0; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)
            
            is_stage = bool(s.get("start_time") and s.get("end_time"))
            current_type = "阶段型" if is_stage else "ddl型"

            # 把 radio 做成胶囊样式（或极小化）
            edit_type = st.radio(
                "日程类型", ["ddl型", "阶段型"],
                index=0 if current_type == "ddl型" else 1,
                horizontal=True, key=f"edit_type_{s['id']}", label_visibility="collapsed"
            )

            deadline_val = datetime.fromisoformat(s["deadline_date"]).date()
            start_val = datetime.fromisoformat(s["start_time"]).time() if s.get("start_time") else time(11, 0)
            end_val = datetime.fromisoformat(s["end_time"]).time() if s.get("end_time") else time(13, 0)
            prep_val = datetime.fromisoformat(s["prep_start"]).date() if s.get("prep_start") else None
            cat_index = cat_names.index(s["category"]) if s["category"] in cat_names else 0

            with st.form(f"edit_{s['id']}_{edit_type}"):
                # 第一排：类别、备注
                f_c1, f_c2 = st.columns(2)
                new_cat = f_c1.selectbox("类别", cat_names, index=cat_index)
                new_note = f_c2.text_input("备注", value=s["note"] or "")
                
                # 第二排：日期、准备日期
                f_c3, f_c4 = st.columns(2)
                new_dl = f_c3.date_input("截止日期", value=deadline_val)
                new_prep = f_c4.date_input("开始准备日期（可选）", value=prep_val if prep_val else today_bj())
                
                # 第三排：时间（如果是阶段型）或直接标签
                if edit_type == "阶段型":
                    f_c5, f_c6, f_c7 = st.columns(3)
                    new_start = f_c5.time_input("开始时间", value=start_val)
                    new_end = f_c6.time_input("结束时间", value=end_val)
                    with f_c7:
                        new_tags = st.multiselect("标签", options=list(tag_map.keys()), default=s["tag_ids"], format_func=lambda tid: tag_map[tid])
                else:
                    new_start, new_end = None, None
                    new_tags = st.multiselect("标签", options=list(tag_map.keys()), default=s["tag_ids"], format_func=lambda tid: tag_map[tid])
                
                # 保存按钮靠右
                _, btn_col = st.columns([4, 1])
                with btn_col:
                    saved = st.form_submit_button("保存修改", use_container_width=True)

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
