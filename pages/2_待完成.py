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
        # ========== 第一行：信息展示 ==========
        # 动态调整列宽，让间距看起来更舒服
        col_cat, col_note, col_date, col_overdue = st.columns([2, 4, 2, 2.5])
        
        with col_cat:
            st.markdown(f"**{s['category']}**")
            
        with col_note:
            # 备注如果不是空的才显示
            if s.get('note'):
                st.markdown(f"<span style='color: #475569;'>{s['note']}</span>", unsafe_allow_html=True)
                
        with col_date:
            date_str = datetime.fromisoformat(s['deadline_date']).strftime("%Y-%m-%d")
            st.markdown(f"<span style='color: #94A3B8; font-size: 0.9em;'>截止: {date_str}</span>", unsafe_allow_html=True)
            
        with col_overdue:
            if s["status"] == "overdue":
                st.markdown(f"<span style='color:#EF4444; font-size: 0.9em; font-weight:500;'>⏰ 逾期 {s['overdue_days']} 天</span>", unsafe_allow_html=True)

        # ========== 第二行：标签 ==========
        if s["tag_ids"]:
            tags_html = "<div style='margin-top: 4px; margin-bottom: 8px;'>"
            for tid in s["tag_ids"]:
                if tid in tag_map:
                    tags_html += f"<span class='custom-tag'>{tag_map[tid]}</span>"
            tags_html += "</div>"
            st.markdown(tags_html, unsafe_allow_html=True)

        # ========== 第三行：按钮与编辑区 ==========
        # 左侧放编辑折叠框，右侧放按钮
        c_action, c_empty = st.columns([8, 2])
        
        with c_action:
            with st.expander("✏️ 编辑"):
                # (这里保留你原来的编辑表单代码不变)
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
                    new_cat = st.selectbox("类别", cat_names, index=cat_index)
                    new_note = st.text_input("备注", value=s["note"] or "")
                    new_dl = st.date_input("截止日期", value=deadline_val)

                    if edit_type == "阶段型":
                        col1, col2 = st.columns(2)
                        new_start = col1.time_input("开始时间", value=start_val)
                        new_end = col2.time_input("结束时间", value=end_val)
                    else:
                        new_start, new_end = None, None

                    new_prep = st.date_input("开始准备日期（可选）", value=prep_val if prep_val else today_bj())
                    new_tags = st.multiselect("标签", options=list(tag_map.keys()), default=s["tag_ids"], format_func=lambda tid: tag_map[tid])
                    
                    saved = st.form_submit_button("保存修改", type="primary")

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
                        st.rerun()

        with c_empty:
            # 用两列把按钮并排放在右上角
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                # 自定义绿色主按钮
                green_btn_css = """
                <style>
                div[data-testid="stButton"] > button[kind="primary"] {
                    background-color: #10B981 !important;
                    border-color: #10B981 !important;
                }
                div[data-testid="stButton"] > button[kind="primary"]:hover {
                    background-color: #059669 !important;
                    border-color: #059669 !important;
                }
                </style>
                """
                st.markdown(green_btn_css, unsafe_allow_html=True)
                
                if st.button("完成", key=f"done_{s['id']}", type="primary", use_container_width=True):
                    update(s["id"], user.id, {"status": "completed"})
                    st.rerun()
                    
            with btn_col2:
                if st.button("删除", key=f"del_{s['id']}", use_container_width=True):
                    delete(s["id"], user.id)
                    st.rerun()
