from streamlit_cookies_controller import CookieController

cookie = CookieController()
COOKIE_NAME = "schedule_refresh_token"
COOKIE_DAYS = 30

import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase():
    """创建 Supabase 客户端，缓存起来避免重复连接"""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


def register(email: str, password: str):
    """注册：直接使用邮箱"""
    try:
        resp = get_supabase().auth.sign_up({
            "email": email.strip(),  # strip() 去掉可能的首尾空格
            "password": password
        })
        return resp.user
    except Exception as e:
        st.error(f"注册失败：{e}")
        return None


def login(email: str, password: str):
    """登录：直接使用邮箱"""
    try:
        resp = get_supabase().auth.sign_in_with_password({
            "email": email.strip(),
            "password": password
        })
        st.session_state["user"] = resp.user
        # 把 refresh_token 存进 Cookie，有效期 30 天
        import time
        expires = time.time() + COOKIE_DAYS * 24 * 3600
        cookie.set(COOKIE_NAME, resp.session.refresh_token, expires=expires)
        st.session_state["access_token"] = resp.session.access_token
        return resp.user
    except Exception as e:
        st.error(f"登录失败：{e}")
        return None


def restore_session():
    """在页面加载时调用，尝试用 Cookie 里的 refresh_token 恢复登录态"""
    if "user" in st.session_state:
        return  # 已经登录，不用恢复

    token = cookie.get(COOKIE_NAME)
    if not token:
        return  # 没有 Cookie，未登录

    try:
        resp = get_supabase().auth.refresh_session(token)
        if resp and resp.user:
            st.session_state["user"] = resp.user
            st.session_state["access_token"] = resp.session.access_token
            # 换新的 refresh_token 写回 Cookie
            import time
            expires = time.time() + COOKIE_DAYS * 24 * 3600
            cookie.set(COOKIE_NAME, resp.session.refresh_token, expires=expires)
    except Exception:
        # token 失效或过期，清掉 Cookie
        cookie.remove(COOKIE_NAME)


def logout():
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    cookie.remove(COOKIE_NAME)
    for key in ["user", "access_token"]:
        st.session_state.pop(key, None)
