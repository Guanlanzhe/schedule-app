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

st.title("📅 日程日历")

all_tags = fetch_tags(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}

# 标签筛选
filter_ids = []
if all_tags:
    groups = {}
    for t in all_tags:
        groups.setdefault(t["group_name"], []).append(t)
    for group_name, items in groups.items():
        chosen = st.multiselect(
            f"按{group_name}筛选",
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

calendar(events=events, options=options, key="cal")
