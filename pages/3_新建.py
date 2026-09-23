from datetime import datetime
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import insert

load_style()
user = require_login()

st.title("➕ 新建日程")

with st.form("new_schedule"):
    category = st.selectbox("类别", ["作业", "考试", "汇报", "其它"])
    note = st.text_input("备注（可选）")
    deadline = st.date_input("截止日期")

    col1, col2 = st.columns(2)
    with col1:
        start_t = st.time_input("开始时间（可选）", value=None)
    with col2:
        end_t = st.time_input("结束时间（可选）", value=None)

    prep_start = st.date_input("开始准备日期（可选）", value=None)

    submitted = st.form_submit_button("创建")

if submitted:
    data = {
        "category": category,
        "note": note,
        "deadline_date": str(deadline),
        "prep_start": str(prep_start) if prep_start else None,
    }
    if start_t and end_t:
        data["start_time"] = datetime.combine(deadline, start_t).isoformat()
        data["end_time"] = datetime.combine(deadline, end_t).isoformat()

    insert(user.id, data)
    st.success("创建成功！")
    st.rerun()