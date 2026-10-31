from datetime import datetime, timedelta
import streamlit as st
import httpx
from supabase import create_client
from supabase.lib.client_options import ClientOptions
from streamlit_cookies_controller import CookieController

cookie = CookieController(key="schedule_cookies")
COOKIE_NAME = "schedule_refresh_token"
COOKIE_DAYS = 30


@st.cache_resource
def get_supabase():
    # 1. 创建自定义的 httpx 客户端，强制使用 HTTP/1.1
    custom_httpx_client = httpx.Client(
        http2=False,  # 关键：关闭 HTTP/2，避免 Streamlit Cloud 上的连接断开问题
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=40)
    )
    
    # 2. 将客户端传递给 Supabase
    options = ClientOptions(httpx_client=custom_httpx_client)
    
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
        options=options
    )


def register(email: str, password: str):
    try:
        resp = get_supabase().auth.sign_up({
            "email": email.strip(),
            "password": password
        })
        return resp.user
    except Exception as e:
        st.error(f"注册失败：{e}")
        return None


def login(email: str, password: str):
    try:
        resp = get_supabase().auth.sign_in_with_password({
            "email": email.strip(),
            "password": password
        })
        st.session_state["user"] = resp.user
        st.session_state["access_token"] = resp.session.access_token

        expires = datetime.now() + timedelta(days=COOKIE_DAYS)
        cookie.set(COOKIE_NAME, resp.session.refresh_token, expires=expires)

        # 每次登录时，清空上一个账号可能残留的数据缓存
        st.cache_data.clear()

        return resp.user
    except Exception as e:
        st.error(f"登录失败：{e}")
        return None


def restore_session():
    if "user" in st.session_state:
        return

    token = cookie.get(COOKIE_NAME)
    if not token:
        return

    try:
        resp = get_supabase().auth.refresh_session(token)
        if resp and resp.user:
            st.session_state["user"] = resp.user
            st.session_state["access_token"] = resp.session.access_token
            expires = datetime.now() + timedelta(days=COOKIE_DAYS)
            cookie.set(COOKIE_NAME, resp.session.refresh_token, expires=expires)
    except Exception:
        cookie.remove(COOKIE_NAME)


def logout():
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    cookie.remove(COOKIE_NAME)
    for key in ["user", "access_token"]:
        st.session_state.pop(key, None)
        
    # 【关键】退出登录时，必须清空数据缓存，防止下一个登录的人看到历史画面
    st.cache_data.clear()
