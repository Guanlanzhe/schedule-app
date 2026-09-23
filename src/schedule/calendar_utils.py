# 所有日程统一颜色，不再按类别区分
UNIFIED_COLOR = "#4A90D9"


def darken(hex_color: str, factor: float = 0.75) -> str:
    """颜色加深，用于逾期标记"""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (int(c * factor) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def to_events(schedules: list) -> list:
    """把数据库记录转成 FullCalendar 事件列表。
    颜色统一，标签名以文字形式拼在标题前面。
    """
    events = []
    for s in schedules:
        if s["status"] == "completed":
            continue

        color = UNIFIED_COLOR
        if s["status"] == "overdue":
            color = darken(color)

        # 标题：类别 + 备注 + 标签
        parts = [s["category"]]
        if s["note"]:
            parts.append(s["note"])
        title = " ".join(parts)

        # 标签拼在标题前，用 [xxx] 形式
        tag_names = s.get("tag_names") or []
        if tag_names:
            title = "[" + "/".join(tag_names) + "] " + title

        event = {
            "id": str(s["id"]),
            "title": title,
            "start": s["start_time"] or s["deadline_date"],
            "color": color,
        }
        if s.get("end_time"):
            event["end"] = s["end_time"]

        events.append(event)
    return events
