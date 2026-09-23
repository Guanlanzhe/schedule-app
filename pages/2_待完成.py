from datetime import datetime
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_pending, delete, update
from src.schedule.overdue import refresh_overdue
from src.schedule.tags import fetch_tags

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("📋 待完成日程")

all_tags = fetch_tags(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}

# 标签筛选（多选）
filter_ids = []
if all_tags:
    groups = {}
    for t in all_tags:
        groups.setdefault(t["group_name"], []).append(t)
    for group_name, items in groups.items():
        chosen = st.multiselect(
            f"按{group_name}筛选",
            options=[t["id"] for t in items],
            format_func=lambda tid: next(
                t["name"] for t in items if t["id"] == tid
            ),
            key=f"filter_{group_name}",
        )
        filter_ids.extend(chosen)

pending = fetch_pending(user.id)

# 如果选了标签，只保留命中任意一个的日程
if filter_ids:
    pending = [s for s in pending if set(s["tag_ids"]) & set(filter_ids)]

if not pending:
    st.success("暂无待完成日程 🎉")
    st.stop()

for s in pending:
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            tag = ""
            if s["status"] == "overdue":
                tag = f"⏰ 逾期 {s['overdue_days']} 天"
            tag_names = " ".join(
                f"`{tag_map[tid]}`" for tid in s["tag_ids"] if tid in tag_map
            )
            st.write(
                f"**{s['deadline_date']}** | {s['category']} | "
                f"{s['note'] or ''} {tag} {tag_names}"
            )
        with c2:
            if st.button("✅ 完成", key=f"done_{s['id']}"):
                update(s["id"], user.id, {"status": "completed"})
                st.rerun()
        with c3:
            if st.button("🗑️ 删除", key=f"del_{s['id']}"):
                delete(s["id"], user.id)
                st.rerun()

        # 展开编辑
        with st.expander("✏️ 编辑"):
            with st.form(f"edit_{s['id']}"):
                new_cat = st.selectbox(
                    "类别", ["作业", "考试", "汇报", "其它"],
                    index=["作业", "考试", "汇报", "其它"].index(s["category"])
                )
                new_note = st.text_input("备注", value=s["note"] or "")
                new_dl = st.date_input(
                    "截止日期", value=datetime.fromisoformat(
                        s["deadline_date"]
                    ).date()
                )
                new_tags = st.multiselect(
                    "标签",
                    options=list(tag_map.keys()),
                    default=s["tag_ids"],
                    format_func=lambda tid: tag_map[tid],
                )
                if st.form_submit_button("保存"):
                    update(s["id"], user.id, {
                        "category": new_cat,
                        "note": new_note,
                        "deadline_date": str(new_dl),
                    }, tag_ids=new_tags)
                    st.rerun()
