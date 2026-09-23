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
    st.warning("还没有类别，请先去「5_设置」创建一个类别")
    st.stop()

# 成功提示
if st.session_state.pop("just_created", False):
    st.success("✅ 已创建")

# 初始化表单计数器
if "form_key" not in st.session_state:
    st.session_state["form_key"] = 0

fk = st.session_state["form_key"]

# ===== 类型选择放在表单外，切换时不会丢失其他字段（因为其他字段在表单内，key 稳定）=====
schedule_type = st.radio(
    "日程类型",
    ["ddl型", "阶段型"],
    horizontal=True,
    key=f"type_{fk}",
    help="ddl型：只有截止日期；阶段型：有开始和结束时间"
)

# ===== 表单 =====
with st.form(f"new_schedule_{fk}"):
    category = st.selectbox("类别", [c["name"] for c in all_cats])
    note = st.text_input("备注（可选）")
    deadline = st.date_input("截止日期", value=date.today())

    # 只有阶段型才显示时间范围
    if schedule_type == "阶段型":
        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("开始时间", value=time(11, 0))
        with col2:
            end_t = st.time_input("结束时间", value=time(13, 0))
    else:
        start_t = None
        end_t = None

    prep_start = st.date_input("开始准备日期（可选）", value=date.today())

    # 标签多选
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
                key=f"tag_sel_{group_name}_{fk}",
            )
            selected_tag_ids.extend(chosen)

    submitted = st.form_submit_button("创建")

if submitted:
    # 阶段型才校验时间
    if schedule_type == "阶段型" and end_t <= start_t:
        st.error("结束时间必须晚于开始时间")
    else:
        data = {
            "category": category,
            "note": note,
            "deadline_date": str(deadline),
            "prep_start": str(prep_start) if prep_start else None,
        }
        if schedule_type == "阶段型":
            data["start_time"] = datetime.combine(deadline, start_t).isoformat()
            data["end_time"] = datetime.combine(deadline, end_t).isoformat()
        # ddl型不写 start_time / end_time，数据库里为 NULL

        insert(user.id, data, tag_ids=selected_tag_ids)
        st.session_state["just_created"] = True
        st.session_state["form_key"] += 1
        st.rerun()
