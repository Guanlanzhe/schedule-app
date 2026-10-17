from datetime import datetime
import streamlit as st
from src.ui import load_style, show_login_form
from src.supabase_client import logout
from src.schedule.db import fetch_pending
from src.schedule.overdue import refresh_overdue
from src.time_utils import today_bj

load_style()

if "user" not in st.session_state:
    show_login_form()
    st.stop()

user = st.session_state["user"]

# 侧边栏
with st.sidebar:
    st.markdown(f"### 👋 你好,\n**{user.email.split('@')[0]}**")
    st.divider()
    if st.button("退出登录", use_container_width=True):
        logout()
        st.rerun()

st.title("概览")

refresh_overdue(user.id)
pending = fetch_pending(user.id)

# 数据处理
ddl_items, stage_items = [], []
for s in pending:
    is_stage = bool(s.get("start_time") and s.get("end_time"))
    target = datetime.fromisoformat(s["start_time"]).date() if is_stage else datetime.fromisoformat(s["deadline_date"]).date()
    s["_days_left"] = (target - today_bj()).days
    (stage_items if is_stage else ddl_items).append(s)

ddl_items.sort(key=lambda x: x["_days_left"])
stage_items.sort(key=lambda x: x["_days_left"])

def render_item(s):
    is_overdue = s["_days_left"] < 0
    color = "#EF4444" if is_overdue else "#10B981"
    status_text = f"逾期 {-s['_days_left']} 天" if is_overdue else ("今天截止" if s["_days_left"] == 0 else f"还有 {s['_days_left']} 天")
    
    st.markdown(f"""
    <div style='display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #F1F5F9;'>
        <div style='width: 6px; height: 6px; border-radius: 50%; background-color: {color}; margin-right: 12px;'></div>
        <div style='flex-grow: 1;'>
            <div style='font-weight: 600; color: #1E293B; font-size: 0.95rem;'>{s['category']} <span style='font-weight: 400; color: #64748B;'>{s['note'] or ''}</span></div>
        </div>
        <div style='color: {color}; font-size: 0.85rem; font-weight: 500;'>{status_text}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📌 临近 DDL")
        if not ddl_items:
            st.caption("暂无任务")
        for s in ddl_items[:5]: # 最多显示5个
            render_item(s)

with col2:
    with st.container(border=True):
        st.markdown("### ⏳ 阶段安排")
        if not stage_items:
            st.caption("暂无任务")
        for s in stage_items[:5]:
            render_item(s)
