from datetime import date, datetime
import streamlit as st
from src.schedule.db import fetch_pending, update


def refresh_overdue(user_id: str):
    """把已过截止时间的 pending 改成 overdue。同一天只刷一次。"""
    today = date.today().isoformat()
    if st.session_state.get("overdue_refreshed") == today:
        return

    today_dt = date.today()
    for s in fetch_pending(user_id):
        if s.get("start_time"):
            deadline = datetime.fromisoformat(s["start_time"]).date()
        else:
            deadline = datetime.fromisoformat(s["deadline_date"]).date()

        if deadline < today_dt and s["status"] == "pending":
            update(s["id"], user_id, {
                "status": "overdue",
                "overdue_days": (today_dt - deadline).days
            })

    st.session_state["overdue_refreshed"] = today