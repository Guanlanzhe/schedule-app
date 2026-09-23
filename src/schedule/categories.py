from src.supabase_client import get_supabase


def fetch_categories(user_id: str):
    """取用户全部类别，按创建时间排序"""
    return (
        get_supabase().table("categories")
        .select("*").eq("user_id", user_id)
        .order("created_at").execute().data
    )


def create_category(user_id: str, name: str):
    """新建类别，若已存在则返回已有记录"""
    existing = (
        get_supabase().table("categories")
        .select("*").eq("user_id", user_id).eq("name", name)
        .execute().data
    )
    if existing:
        return existing[0]
    resp = get_supabase().table("categories").insert({
        "user_id": user_id, "name": name
    }).execute()
    return resp.data[0]


def delete_category(cat_id: int, user_id: str):
    return (
        get_supabase().table("categories").delete()
        .eq("id", cat_id).eq("user_id", user_id).execute()
    )
