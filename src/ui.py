import streamlit as st

def load_style():
    """全局页面设置，注入高级自定义 CSS"""
    st.set_page_config(
        page_title="日程管理",
        page_icon="📅",
        layout="wide"
    )
    
    # 全局 CSS 注入
    st.markdown("""
        <style>
        /* 整体背景和字体 */
        .stApp {
            background-color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* 隐藏顶部的默认装饰条 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 调整主标题和副标题 */
        h1 {
            color: #1E293B;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        h2, h3 {
            color: #334155;
            font-weight: 600;
        }
        
        /* 侧边栏样式 */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        
        /* 卡片容器美化 (给 st.container(border=True) 用的) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            padding: 1.5rem;
            transition: all 0.2s ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
        }
        
        /* 按钮美化 */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s;
            border: 1px solid #E2E8F0;
        }
        .stButton > button:hover {
            border-color: #3B82F6;
            color: #3B82F6;
        }
        
        /* 主按钮美化 (比如表单提交按钮) */
        [data-testid="baseButton-primary"] {
            background-color: #2563EB !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="baseButton-primary"]:hover {
            background-color: #1D4ED8 !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }
        
        /* 输入框美化 */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > div, 
        .stDateInput > div > div > input,
        .stTimeInput > div > div > input {
            border-radius: 8px;
        }
        
        /* 标签(Tag)样式 */
        .custom-tag {
            display: inline-block;
            background-color: #EFF6FF;
            color: #2563EB;
            padding: 2px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-right: 6px;
            margin-top: 4px;
        }
        </style>
    """, unsafe_allow_html=True)


def require_login():
    from src.supabase_client import restore_session
    restore_session()
    if "user" not in st.session_state:
        st.warning("请先登录")
        st.stop()
    return st.session_state["user"]


def show_login_form():
    from src.supabase_client import restore_session

    # 先尝试从 Cookie 恢复登录态
    restore_session()
    # 恢复成功后立即 rerun，让主页重新判断
    if "user" in st.session_state:
        st.rerun()

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
