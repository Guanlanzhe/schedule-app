import streamlit as st
from streamlit_calendar import calendar
from src.ui import load_style, require_login
from src.schedule.db import fetch_all
from src.schedule.overdue import refresh_overdue
from src.schedule.calendar_utils import to_events
from src.schedule.tags import fetch_tags

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("日程日历")
st.write("") # 留出一点空白，呼吸感

all_tags = fetch_tags(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}

# 使用折叠框收纳筛选器
with st.expander("🔍 筛选标签", expanded=False):
    filter_ids = []
    if all_tags:
        groups = {}
        for t in all_tags:
            groups.setdefault(t["group_name"], []).append(t)
            
        # 把标签按多列排布，不会显得太挤
        cols = st.columns(len(groups) if len(groups) > 0 else 1)
        for i, (group_name, items) in enumerate(groups.items()):
            with cols[i % len(groups)]:
                chosen = st.multiselect(
                    f"{group_name}",
                    options=[t["id"] for t in items],
                    format_func=lambda tid: next(
                        t["name"] for t in items if t["id"] == tid
                    ),
                    key=f"cal_filter_{group_name}",
                )
                filter_ids.extend(chosen)

schedules = fetch_all(user.id)
if filter_ids:
    schedules = [s for s in schedules if set(s["tag_ids"]) & set(filter_ids)]

events = to_events(schedules)

# 日历配置
options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
    },
    "buttonText": {
        "today": "今天", "month": "月", "week": "周",
        "day": "日", "list": "列表",
    },
    "allDayText": "全天",
    "moreLinkText": "还有更多",
    "noEventsText": "没有日程",
    "editable": False,
    "selectable": False,
}

# 渲染日历
calendar(events=events, options=options, key="cal")

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
