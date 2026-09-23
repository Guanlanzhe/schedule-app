import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase():
    """创建 Supabase 客户端，缓存起来避免重复连接"""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


def register(username: str, password: str):
    """注册：用伪邮箱绕过邮箱验证"""
    email = f"{username}@schedule.local"
    try:
        resp = get_supabase().auth.sign_up({
            "email": email,
            "password": password
        })
        return resp.user
    except Exception as e:
        st.error(f"注册失败：{e}")
        return None


def login(username: str, password: str):
    """登录：同样用伪邮箱"""
    email = f"{username}@schedule.local"
    try:
        resp = get_supabase().auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        # 把登录态存到 session_state
        st.session_state["user"] = resp.user
        st.session_state["access_token"] = resp.session.access_token
        return resp.user
    except Exception as e:
        st.error(f"登录失败：{e}")
        return None


def logout():
    """退出登录，清空 session"""
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    for key in ["user", "access_token"]:
        st.session_state.pop(key, None)