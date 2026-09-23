from datetime import datetime, date
import streamlit as st
from src.ui import load_style
from src.supabase_client import logout
from src.ui import show_login_form
from src.schedule.db import fetch_pending
from src.schedule.overdue import refresh_overdue

load_style()

# 未登录 → 显示登录表单
if "user" not in st.session_state:
    show_login_form()
    st.stop()

# 已登录
user = st.session_state["user"]

st.sidebar.write(f"👋 {user.email}")
if st.sidebar.button("退出登录"):
    logout()
    st.rerun()

st.title("📅 日程管理主页")
st.subheader("日程提醒")

refresh_overdue(user.id)

# 取所有未完成日程（含逾期）
pending = fetch_pending(user.id)

# 按类型拆分
ddl_items = []
stage_items = []

for s in pending:
    is_stage = bool(s.get("start_time") and s.get("end_time"))

    # 计算剩余天数：阶段型按 start_time，ddl型按 deadline_date
    if is_stage:
        target = datetime.fromisoformat(s["start_time"]).date()
    else:
        target = datetime.fromisoformat(s["deadline_date"]).date()

    days_left = (target - date.today()).days
    s["_days_left"] = days_left

    if is_stage:
        stage_items.append(s)
    else:
        ddl_items.append(s)

# 排序：按剩余天数升序（最紧迫的在上）
ddl_items.sort(key=lambda x: x["_days_left"])
stage_items.sort(key=lambda x: x["_days_left"])


def format_days(days_left: int) -> str:
    """把剩余天数格式化成中文提示"""
    if days_left > 0:
        return f"还剩 {days_left} 天"
    elif days_left == 0:
        return "今天截止"
    else:
        return f"已逾期 {-days_left} 天"


def render_item(s: dict):
    """渲染单条提醒"""
    is_overdue = s["status"] == "overdue" or s["_days_left"] < 0
    color = "🔴" if is_overdue else "🟢"
    st.write(
        f"{color} **{s['category']}** | {s['note'] or '（无备注）'}  \n"
        f"&nbsp;&nbsp;&nbsp;&nbsp;{format_days(s['_days_left'])}"
    )


col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📌 ddl 提醒")
    if not ddl_items:
        st.caption("暂无 ddl 型日程")
    else:
        for s in ddl_items:
            render_item(s)

with col2:
    st.markdown("### ⏳ 阶段型日程提醒")
    if not stage_items:
        st.caption("暂无阶段型日程")
    else:
        for s in stage_items:
            render_item(s)
