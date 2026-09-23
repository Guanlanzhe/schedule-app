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
