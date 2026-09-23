from datetime import datetime, date, time
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import insert
from src.schedule.tags import fetch_tags
from src.schedule.categories import fetch_categories

load_style()
user = require_login()

st.title("➕ 新建日程")

all_tags = fetch_tags(user.id)
all_cats = fetch_categories(user.id)

if not all_cats:
    st.warning("还没有类别，请先去「5_标签管理」创建一个类别")
    st.stop()

with st.form("new_schedule"):
    category = st.selectbox("类别", [c["name"] for c in all_cats])
    note = st.text_input("备注（可选）")
    deadline = st.date_input("截止日期", value=date.today())

    col1, col2 = st.columns(2)
    with col1:
        start_t = st.time_input("开始时间（可选）", value=time(11, 0))
    with col2:
        end_t = st.time_input("结束时间（可选）", value=time(13, 0))

    prep_start = st.date_input("开始准备日期（可选）", value=date.today())

    selected_tag_ids = []
    if all_tags:
        st.write("**标签（可多选）**")
        groups = {}
        for t in all_tags:
            groups.setdefault(t["group_name"], []).append(t)
        for group_name, items in groups.items():
            st.caption(group_name)
            chosen = st.multiselect(
                label=f"选择{group_name}标签",
                options=[t["id"] for t in items],
                format_func=lambda tid: next(
                    t["name"] for t in items if t["id"] == tid
                ),
                label_visibility="collapsed",
                key=f"tag_sel_{group_name}",
            )
            selected_tag_ids.extend(chosen)

    submitted = st.form_submit_button("创建")

if submitted:
    if end_t <= start_t:
        st.error("结束时间必须晚于开始时间")
    else:
        data = {
            "category": category,
            "note": note,
            "deadline_date": str(deadline),
            "prep_start": str(prep_start) if prep_start else None,
            "start_time": datetime.combine(deadline, start_t).isoformat(),
            "end_time": datetime.combine(deadline, end_t).isoformat(),
        }
        insert(user.id, data, tag_ids=selected_tag_ids)
        st.success("创建成功！")
        st.rerun()
