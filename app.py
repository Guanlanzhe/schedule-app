from datetime import datetime, date
import streamlit as st
from src.ui import load_style, show_login_form
from src.supabase_client import logout
from src.schedule.db import fetch_pending
from src.schedule.overdue import refresh_overdue
from src.time_utils import today_bj  # 引入你写好的北京时间函数

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
    if is_stage:
        target = datetime.fromisoformat(s["start_time"]).date()
    else:
        target = datetime.fromisoformat(s["deadline_date"]).date()

    days_left = (target - today_bj()).days
    s["_days_left"] = days_left

    if is_stage:
        stage_items.append(s)
    else:
        ddl_items.append(s)

ddl_items.sort(key=lambda x: x["_days_left"])
stage_items.sort(key=lambda x: x["_days_left"])

def format_days(days_left: int) -> str:
    if days_left > 0:
        return f"还剩 {days_left} 天"
    elif days_left == 0:
        return "今天截止"
    else:
        return f"已逾期 {-days_left} 天"

def render_item(s: dict):
    """渲染单条提醒（高级版）"""
    is_overdue = s["status"] == "overdue" or s["_days_left"] < 0
    # 颜色标识：正常为绿色，逾期为红色
    dot_color = "#EF4444" if is_overdue else "#10B981"
    
    # 构建 HTML
    html = f"""
    <div style='display: flex; align-items: start; margin-bottom: 12px;'>
        <div style='width: 8px; height: 8px; border-radius: 50%; background-color: {dot_color}; margin-top: 6px; margin-right: 12px; flex-shrink: 0;'></div>
        <div style='flex-grow: 1;'>
            <div style='font-size: 1em; font-weight: 600; color: #1E293B;'>{s['category']} <span style='font-weight: 400; color: #475569;'>{s['note'] or ''}</span></div>
            <div style='font-size: 0.85em; color: #94A3B8; margin-top: 2px;'>{format_days(s['_days_left'])}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("<h3 style='font-size: 1.2rem; margin-bottom: 1rem;'>📌 DDL 提醒</h3>", unsafe_allow_html=True)
        if not ddl_items:
            st.caption("暂无 ddl 型日程")
        else:
            for s in ddl_items:
                render_item(s)

with col2:
    with st.container(border=True):
        st.markdown("<h3 style='font-size: 1.2rem; margin-bottom: 1rem;'>⏳ 阶段型日程提醒</h3>", unsafe_allow_html=True)
        if not stage_items:
            st.caption("暂无阶段型日程")
        else:
            for s in stage_items:
                render_item(s)
