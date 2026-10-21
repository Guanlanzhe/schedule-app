import streamlit as st

def load_style():
    st.set_page_config(
        page_title="日程管理",
        page_icon="📅",
        layout="wide"
    )
    
    st.markdown("""
        <style>
        /* 1. 全局字体与背景：英文 Times New Roman，中文宋体 */
        html, body, [class*="css"] {
            font-family: 'Times New Roman', SimSun, 'Songti SC', STSong, serif !important;
            line-height: 1.6 !important; /* 宋体需要稍微大一点的行高才好看 */
        }
        .stApp {
            background-color: #F8FAFC;
        }
        
        /* 2. 隐藏默认冗余元素 (精准隐藏，避免误伤日历) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {visibility: hidden;}
        
        /* 3. 卡片容器 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* 4. 输入框美化 */
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
            background-color: #F1F5F9 !important;
            border-radius: 8px !important;
            border: 1px solid transparent !important;
            transition: all 0.2s ease;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border-color: #3B82F6 !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }
        input, textarea {
            background-color: transparent !important;
            border: none !important;
            font-family: 'Times New Roman', SimSun, serif !important; /* 输入框也同步 */
        }
        
        /* 5. 按钮美化 */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            font-family: 'Times New Roman', SimSun, serif !important; /* 按钮同步 */
        }
        .stButton > button:hover {
            border-color: #3B82F6 !important;
            color: #3B82F6 !important;
        }
        
        /* 主按钮 */
        [data-testid="baseButton-primary"] {
            background-color: #2563EB !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="baseButton-primary"]:hover {
            background-color: #1D4ED8 !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }
        
        /* 7. 文本排版 */
        h1 { 
            font-size: 2rem !important; 
            font-weight: 700 !important; 
            color: #1E293B !important; 
            letter-spacing: -0.5px; 
            padding-bottom: 0rem !important;
            font-family: 'Times New Roman', SimSun, serif !important;
        }
        h2, h3 { 
            font-weight: 600 !important; 
            color: #334155 !important; 
            padding-bottom: 0.5rem !important;
            font-family: 'Times New Roman', SimSun, serif !important;
        }
        
        /* 8. 修复日期选择器（日历）被全局样式破坏的问题 */
        div[data-baseweb="calendar"] button {
            visibility: visible !important;
            display: block !important;
        }
        div[data-baseweb="calendar"] h2,
        div[data-baseweb="calendar"] div[role="heading"] {
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: #1E293B !important;
            visibility: visible !important;
            display: block !important;
            font-family: 'Times New Roman', SimSun, serif !important;
        }
        div[data-baseweb="popover"] {
            z-index: 9999 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def require_login():
    from src.supabase_client import restore_session
    restore_session()
    if "user" not in st.session_state:
        # 自定义提示框，比原生的 st.warning 更美观
        st.markdown("""
        <div style='background-color: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;'>
            🔒 您还未登录，请先登录以查看此页面。
        </div>
        """, unsafe_allow_html=True)
        
        # 居中放置登录按钮
        _, c, _ = st.columns([1, 2, 1])
        with c:
            if st.button("🔑 去登录", type="primary", use_container_width=True):
                st.switch_page("app.py") # 确保你的主文件叫 app.py，如果叫主页.py 请改成 "主页.py"
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
