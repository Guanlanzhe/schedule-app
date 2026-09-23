import streamlit as st
from streamlit_calendar import calendar
from src.ui import load_style, require_login
from src.schedule.db import fetch_all
from src.schedule.overdue import refresh_overdue
from src.schedule.calendar_utils import to_events

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("📅 日程日历")

schedules = fetch_all(user.id)
events = to_events(schedules)

options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
    },
    "editable": False,
    "selectable": False,
    "locale": "zh-cn",
}

result = calendar(events=events, options=options, key="cal")

# 点击事件 → 存进 session_state，跳到待完成页处理
if result and result.get("callback") == "eventClick":
    st.session_state["selected_event_id"] = int(result["eventClick"]["event"]["id"])
    st.info("已选中该日程，请去「2_待完成」页面操作")