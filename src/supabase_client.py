from datetime import datetime, timedelta
import streamlit as st
from supabase import create_client
from streamlit_cookies_controller import CookieController

cookie = CookieController(key="schedule_cookies")
COOKIE_NAME = "schedule_refresh_token"
COOKIE_DAYS = 30


@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
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
