CATEGORY_COLORS = {
    "作业": "#4A90D9",   # 蓝色
    "考试": "#D94A4A",   # 红色
    "汇报": "#50B86C",   # 绿色
    "其它": "#B8B8B8",   # 灰色
}


def darken(hex_color: str, factor: float = 0.75) -> str:
    """颜色加深，用于逾期标记"""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (int(c * factor) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def to_events(schedules: list) -> list:
    """把数据库记录转成 FullCalendar 需要的事件列表"""
    events = []
    for s in schedules:
        if s["status"] == "completed":
            continue  # 已完成的不显示在日历上

        color = CATEGORY_COLORS.get(s["category"], "#999")
        if s["status"] == "overdue":
            color = darken(color)

        event = {
            "id": str(s["id"]),
            "title": f"[{s['category']}] {s['note'] or ''}".strip(),
            "start": s["start_time"] or s["deadline_date"],
            "color": color,
        }
        if s.get("end_time"):
            event["end"] = s["end_time"]

        events.append(event)
    return events