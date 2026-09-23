from src.supabase_client import get_supabase
from src.schedule.tags import fetch_schedule_tags


def _attach_tags(user_id: str, schedules: list) -> list:
    """给每条日程附上 tag_ids 列表"""
    mapping = fetch_schedule_tags(user_id)
    for s in schedules:
        s["tag_ids"] = mapping.get(s["id"], [])
    return schedules


def fetch_all(user_id: str):
    data = (
        get_supabase().table("schedules")
        .select("*").eq("user_id", user_id)
        .order("deadline_date").execute().data
    )
    return _attach_tags(user_id, data)


def fetch_pending(user_id: str):
    data = (
        get_supabase().table("schedules")
        .select("*").eq("user_id", user_id)
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
    return resp


def update(sid: int, user_id: str, updates: dict, tag_ids: list[int] = None):
    resp = (
        get_supabase().table("schedules")
        .update(updates).eq("id", sid).eq("user_id", user_id).execute()
    )
    if tag_ids is not None:
        from src.schedule.tags import set_schedule_tags
        set_schedule_tags(sid, tag_ids)
    return resp


def delete(sid: int, user_id: str):
    return (
        get_supabase().table("schedules")
        .delete().eq("id", sid).eq("user_id", user_id).execute()
    )
