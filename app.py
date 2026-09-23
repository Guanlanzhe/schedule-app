import streamlit as st
from src.ui import load_style, show_login_form, require_login
from src.supabase_client import logout

load_style()

# 未登录 → 显示登录表单
if "user" not in st.session_state:
    show_login_form()
    st.stop()

# 已登录 → 显示主页
user = st.session_state["user"]

st.sidebar.write(f"👋 {user.email}")
if st.sidebar.button("退出登录"):
    logout()
    st.rerun()

st.title("📅 日程管理主页")
st.write("请从左侧边栏选择功能页面：")
st.markdown("""
- **1_日历**：月/周/日视图查看所有日程
- **2_待完成**：按截止时间排序的待办列表
- **3_新建**：创建新日程
- **4_统计**：未完成数量、分类统计、柱状图
""")