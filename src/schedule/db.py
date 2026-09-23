from src.supabase_client import get_supabase


def fetch_all(user_id: str):
    """取当前用户全部日程，按截止日期排序"""
    return (
        get_supabase().table("schedules")
        .select("*")
        .eq("user_id", user_id)
        .order("deadline_date")
        .execute()
        .data
    )


def fetch_pending(user_id: str):
    """取待完成（含逾期）的日程"""
    return (
        get_supabase().table("schedules")
        .select("*")
        .eq("user_id", user_id)
        .in_("status", ["pending", "overdue"])
        .order("deadline_date")
        .execute()
        .data
    )


def insert(user_id: str, data: dict):
    """插入一条日程"""
    data["user_id"] = user_id
    return get_supabase().table("schedules").insert(data).execute()


def update(sid: int, user_id: str, updates: dict):
    """更新一条日程，user_id 作为双保险"""
    return (
        get_supabase().table("schedules")
        .update(updates)
        .eq("id", sid)
        .eq("user_id", user_id)
        .execute()
    )


def delete(sid: int, user_id: str):
    """物理删除一条日程"""
    return (
        get_supabase().table("schedules")
        .delete()
        .eq("id", sid)
        .eq("user_id", user_id)
        .execute()
    )