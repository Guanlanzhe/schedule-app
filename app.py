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
st.write("")

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

# 生成卡片内列表的 HTML
def build_list_html(items, empty_text="暂无任务"):
    if not items:
        return f"<div style='color: #94A3B8; font-size: 0.95rem; padding: 10px 0;'>{empty_text}</div>"
    
    html = "<div style='display: flex; flex-direction: column;'>"
    
    for i, s in enumerate(items[:6]): # 最多显示 6 个
        is_overdue = s["_days_left"] < 0
        color = "#EF4444" if is_overdue else "#10B981"
        status_text = f"逾期 {-s['_days_left']} 天" if is_overdue else ("今天截止" if s["_days_left"] == 0 else f"还有 {s['_days_left']} 天")
        
        border_style = "border-bottom: 1px solid #F1F5F9; padding-bottom: 12px; margin-bottom: 12px;" if i < len(items[:6]) - 1 else ""
        
        # 用 margin-left 强制拉开至少 15px 的距离
        html += f"""<div style='display: flex; align-items: flex-start; {border_style}'>
<div style='width: 6px; height: 6px; border-radius: 50%; background-color: {color}; margin-top: 8px; margin-right: 12px; flex-shrink: 0;'></div>
<div style='flex-grow: 1; min-width: 0;'>
<div style='font-weight: 600; color: #1E293B; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
{s['category']} <span style='font-weight: 400; color: #64748B; margin-left: 15px;'>{s['note'] or ''}</span>
</div>
</div>
<div style='color: {color}; font-size: 0.85rem; font-weight: 500; white-space: nowrap; margin-left: 20px; margin-top: 2px;'>
{status_text}
</div>
</div>"""
    
    html += "</div>"
    return html


col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""<div style='background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
<h3 style='margin-top: 0; margin-bottom: 1.2rem; font-size: 1.15rem; font-weight: 600; color: #1E293B; display: flex; align-items: center; gap: 8px;'>
<span style='font-size: 1.3rem;'>📌</span> 临近 DDL
</h3>
{build_list_html(ddl_items, "暂无临近 DDL")}
</div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div style='background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
<h3 style='margin-top: 0; margin-bottom: 1.2rem; font-size: 1.15rem; font-weight: 600; color: #1E293B; display: flex; align-items: center; gap: 8px;'>
<span style='font-size: 1.3rem;'>⏳</span> 阶段安排
</h3>
{build_list_html(stage_items, "暂无阶段安排")}
</div>""", unsafe_allow_html=True)

st.write("")
st.divider()

st.markdown("### 🚀 快捷导航")
# 使用 5 列并排展示链接，如果不需要图标可以去掉 icon 参数
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.page_link("pages/1_日历.py", label="日程日历", icon="📅")
with c2:
    st.page_link("pages/2_待完成.py", label="待办事项", icon="📋")
with c3:
    st.page_link("pages/3_新建.py", label="新建任务", icon="➕")
with c4:
    st.page_link("pages/4_统计.py", label="数据统计", icon="📊")
with c5:
    st.page_link("pages/5_设置.py", label="标签设置", icon="⚙️")
