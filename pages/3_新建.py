from datetime import datetime, time
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import insert
from src.schedule.tags import fetch_tags
from src.schedule.categories import fetch_categories
from src.time_utils import today_bj

load_style()
user = require_login()

st.title("新建任务")
st.write("")

all_tags = fetch_tags(user.id)
all_cats = fetch_categories(user.id)

if not all_cats:
    st.warning("请先去「设置」添加类别")
    st.stop()

# 居中布局：左中右按 1:2:1 分栏
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    with st.container(border=True):
        # 类型切换放在表单外
        schedule_type = st.radio("日程类型", ["ddl型", "阶段型"], horizontal=True, help="ddl型没有具体时段")
        
        if "form_key" not in st.session_state:
            st.session_state["form_key"] = 0
        fk = st.session_state["form_key"]

        with st.form(f"new_schedule_{fk}"):
            category = st.selectbox("类别", [c["name"] for c in all_cats])
            note = st.text_input("任务名称/备注")
            
            deadline = st.date_input("截止日期", value=today_bj())
            
            if schedule_type == "阶段型":
                c1, c2 = st.columns(2)
                start_t = c1.time_input("开始时间", value=time(11, 0))
                end_t = c2.time_input("结束时间", value=time(13, 0))
            else:
                start_t, end_t = None, None
                
            prep_start = st.date_input("开始准备日期", value=today_bj())
            
            # 标签选择
            selected_tag_ids = []
            if all_tags:
                groups = {}
                for t in all_tags:
                    groups.setdefault(t["group_name"], []).append(t)
                for group_name, items in groups.items():
                    chosen = st.multiselect(
                        f"{group_name}",
                        options=[t["id"] for t in items],
                        format_func=lambda tid: next(t["name"] for t in items if t["id"] == tid),
                        key=f"tag_{group_name}_{fk}"
                    )
                    selected_tag_ids.extend(chosen)
            
            st.write("")
            submitted = st.form_submit_button("确认创建", type="primary", use_container_width=True)

        if submitted:
            if schedule_type == "阶段型" and end_t <= start_t:
                st.error("结束时间必须晚于开始时间")
            else:
                data = {
                    "category": category, "note": note, "deadline_date": str(deadline),
                    "prep_start": str(prep_start)
                }
                if schedule_type == "阶段型":
                    data["start_time"] = datetime.combine(deadline, start_t).isoformat()
                    data["end_time"] = datetime.combine(deadline, end_t).isoformat()
                    
                insert(user.id, data, tag_ids=selected_tag_ids)
                st.session_state["form_key"] += 1
                st.success("已成功创建！")
                st.rerun()

# ====== 底部：回到主页 ======
st.write("")
st.write("")
st.divider()

# 限制按钮宽度，看起来更精致，不会占满全屏
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    # type="primary" 会让按钮变成我们之前设置的高级蓝色
    if st.button("🏠 回到主页", use_container_width=True, type="primary"):
        st.switch_page("app.py")
