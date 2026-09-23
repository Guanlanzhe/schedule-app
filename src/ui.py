import streamlit as st


def load_style():
    """全局页面设置，每个页面开头调用一次"""
    st.set_page_config(
        page_title="日程管理",
        page_icon="📅",
        layout="wide"
    )


def require_login():
    """页面门卫：没登录就停住，返回当前用户"""
    if "user" not in st.session_state:
        st.warning("请先登录")
        st.stop()
    return st.session_state["user"]


def show_login_form():
    st.title("📅 临床医学生日程管理")

    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("邮箱")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录")
        if submitted:
            from src.supabase_client import login
            user = login(email, password)
            if user:
                st.rerun()

    with tab2:
        with st.form("register_form"):
            email = st.text_input("邮箱")
            password = st.text_input("密码（至少6位）", type="password")
            submitted = st.form_submit_button("注册")
        if submitted:
            from src.supabase_client import register
            user = register(email, password)
            if user:
                st.success("注册成功，请查收验证邮件")
