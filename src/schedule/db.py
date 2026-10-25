import streamlit as st
from src.supabase_client import get_supabase
from src.schedule.tags import fetch_schedule_tags, fetch_tags

def _attach_tags(user_id: str, schedules: list) -> list:
    """给每条日程附上 tag_ids 和 tag_names"""
    mapping = fetch_schedule_tags(user_id)
    all_tags = {t["id"]: t["name"] for t in fetch_tags(user_id)}
    for s in schedules:
        ids = mapping.get(s["id"], [])
        s["tag_ids"] = ids
        s["tag_names"] = [all_tags[tid] for tid in ids if tid in all_tags]
    return schedules

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all(user_id: str):
    """拉取全部数据，缓存 60 秒"""
    data = (
        get_supabase().table("schedules")
        .select("*")
        .eq("user_id", user_id)  # <--- 核心过滤：必须是当前用户的 ID
        .order("deadline_date").execute().data
    )
    return _attach_tags(user_id, data)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_pending(user_id: str):
    """拉取待完成数据，缓存 60 秒"""
    data = (
        get_supabase().table("schedules")
        .select("*")
        .eq("user_id", user_id)  # <--- 核心过滤：必须是当前用户的 ID
        .in_("status", ["pending", "overdue"])
        .order("deadline_date").execute().data
    )
    return _attach_tags(user_id, data)

def insert(user_id: str, data: dict, tag_ids: list[int] = None):
    data["user_id"] = user_id
    resp = get_supabase().table("schedules").insert(data).execute()
    new_id = resp.data[0]["id"]
    if tag_ids:
        from src.schedule.tags import set_schedule_tags
        set_schedule_tags(new_id, tag_ids)
    st.cache_data.clear()  # 插入后清空缓存
    return resp

def update(sid: int, user_id: str, updates: dict, tag_ids: list[int] = None):
    resp = (
        get_supabase().table("schedules")
        .update(updates)
        .eq("id", sid)
        .eq("user_id", user_id)  # <--- 核心过滤：只能改自己的
        .execute()
    )
    if tag_ids is not None:
        from src.schedule.tags import set_schedule_tags
        set_schedule_tags(sid, tag_ids)
    st.cache_data.clear()  # 更新后清空缓存
    return resp

def delete(sid: int, user_id: str):
    resp = (
        get_supabase().table("schedules")
        .delete()
        .eq("id", sid)
        .eq("user_id", user_id)  # <--- 核心过滤：只能删自己的
        .execute()
    )
    st.cache_data.clear()  # 删除后清空缓存
    return resp
