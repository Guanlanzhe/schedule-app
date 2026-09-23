import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_pending, delete, update
from src.schedule.overdue import refresh_overdue

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("📋 待完成日程")

pending = fetch_pending(user.id)

if not pending:
    st.success("暂无待完成日程 🎉")
    st.stop()

for s in pending:
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            tag = ""
            if s["status"] == "overdue":
                tag = f"⏰ 逾期 {s['overdue_days']} 天"
            st.write(
                f"**{s['deadline_date']}** | {s['category']} | "
                f"{s['note'] or ''} {tag}"
            )
        with c2:
            if st.button("✅ 完成", key=f"done_{s['id']}"):
                update(s["id"], user.id, {"status": "completed"})
                st.rerun()
        with c3:
            if st.button("🗑️ 删除", key=f"del_{s['id']}"):
                delete(s["id"], user.id)
                st.rerun()