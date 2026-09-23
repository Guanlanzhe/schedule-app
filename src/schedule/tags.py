from src.supabase_client import get_supabase


def fetch_tags(user_id: str):
    """取用户全部标签，按分类名、标签名排序"""
    return (
        get_supabase().table("tags")
        .select("*").eq("user_id", user_id)
        .order("group_name").order("name")
        .execute().data
    )


def create_tag(user_id: str, name: str, group_name: str):
    """新建标签，若已存在则返回已有记录"""
    existing = (
        get_supabase().table("tags")
        .select("*").eq("user_id", user_id).eq("name", name)
        .execute().data
    )
    if existing:
        return existing[0]
    resp = get_supabase().table("tags").insert({
        "user_id": user_id, "name": name, "group_name": group_name
    }).execute()
    return resp.data[0]


def delete_tag(tag_id: int, user_id: str):
    return (
        get_supabase().table("tags").delete()
        .eq("id", tag_id).eq("user_id", user_id).execute()
    )


def fetch_schedule_tags(user_id: str):
    """取所有 日程-标签 关联，返回 {schedule_id: [tag_id, ...]}"""
    # 先取该用户所有日程 id
    sids = [
        s["id"] for s in
        get_supabase().table("schedules").select("id")
        .eq("user_id", user_id).execute().data
    ]
    if not sids:
        return {}
    rows = (
        get_supabase().table("schedule_tags").select("*")
        .in_("schedule_id", sids).execute().data
    )
    result = {}
    for r in rows:
        result.setdefault(r["schedule_id"], []).append(r["tag_id"])
    return result


def set_schedule_tags(schedule_id: int, tag_ids: list[int]):
    """覆盖式更新某日程的标签"""
    sb = get_supabase()
    sb.table("schedule_tags").delete().eq("schedule_id", schedule_id).execute()
    if tag_ids:
        sb.table("schedule_tags").insert([
            {"schedule_id": schedule_id, "tag_id": tid} for tid in tag_ids
        ]).execute()
