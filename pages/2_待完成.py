from datetime import datetime, date, time
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_pending, delete, update
from src.schedule.overdue import refresh_overdue
from src.schedule.tags import fetch_tags
from src.schedule.categories import fetch_categories
from src.time_utils import today_bj

load_style()
user = require_login()
refresh_overdue(user.id)

st.title("待办事项")
st.write("")

# 局部 CSS：只作用于当前页面，让右侧按钮在高度上和左侧文本完美对齐
st.markdown("""
<style>
    /* 强制按钮所在列垂直居中 */
    div[data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

all_tags = fetch_tags(user.id)
all_cats = fetch_categories(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}
cat_names = [c["name"] for c in all_cats]

# 筛选器
with st.expander("🔍 筛选", expanded=False):
    filter_ids = []
    if all_tags:
        groups = {}
        for t in all_tags:
            groups.setdefault(t["group_name"], []).append(t)
        cols = st.columns(len(groups))
        for i, (group_name, items) in enumerate(groups.items()):
            with cols[i % len(groups)]:
                chosen = st.multiselect(
                    f"{group_name}",
                    options=[t["id"] for t in items],
                    format_func=lambda tid: next(t["name"] for t in items if t["id"] == tid),
                    key=f"filter_{group_name}",
                )
                filter_ids.extend(chosen)

pending = fetch_pending(user.id)
if filter_ids:
    pending = [s for s in pending if set(s["tag_ids"]) & set(filter_ids)]

if not pending:
    st.success("太棒了，没有待办事项！")
    st.stop()

for s in pending:
    with st.container(border=True):
        c_info, c_actions = st.columns([7.5, 2.5])
        
        with c_info:
            # 动态生成左侧 HTML 信息
            title_html = f"<div style='font-size: 1.05rem; font-weight: 600; color: #1E293B; line-height: 1.4;'>"
            title_html += f"{s['category']}"
            
            # 【核心修复】：使用 margin-left 强行拉开 15px 距离
            if s['note']:
                title_html += f"<span style='font-weight: 400; color: #475569; margin-left: 15px;'>{s['note']}</span>"
            
            # 标签内联（同样使用 margin-left 拉开）
            if s["tag_ids"]:
                for tid in s["tag_ids"]:
                    if tid in tag_map:
                        title_html += f"<span style='font-size: 0.75rem; color: #2563EB; background-color: #EFF6FF; padding: 2px 6px; border-radius: 4px; vertical-align: middle; font-weight: 400; margin-left: 12px;'>{tag_map[tid]}</span>"
            title_html += "</div>"
            
            # 副标题：时间与逾期状态
            date_str = datetime.fromisoformat(s['deadline_date']).strftime("%Y-%m-%d")
            meta_html = f"<div style='font-size: 0.85rem; color: #94A3B8; margin-top: 6px;'>"
            if s["status"] == "overdue":
                meta_html += f"<span style='color: #EF4444; font-weight: 500;'>逾期 {s['overdue_days']} 天</span> &nbsp;·&nbsp; "
            meta_html += f"截止: {date_str}</div>"
            
            st.markdown(title_html + meta_html, unsafe_allow_html=True)
            
        with c_actions:
            c_e, c_d, c_del = st.columns(3)
            edit_key = f"toggle_edit_{s['id']}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
                
            with c_e:
                if st.button("收起" if st.session_state[edit_key] else "编辑", key=f"btn_edit_{s['id']}", use_container_width=True):
                    st.session_state[edit_key] = not st.session_state[edit_key]
                    st.rerun()
            with c_d:
                if st.button("完成", key=f"done_{s['id']}", use_container_width=True):
                    update(s["id"], user.id, {"status": "completed"})
                    st.rerun()
            with c_del:
                if st.button("删除", key=f"del_{s['id']}", use_container_width=True):
                    delete(s["id"], user.id)
                    st.rerun()

        # ========== 编辑区 ==========
        if st.session_state[edit_key]:
            st.divider()
            is_stage = bool(s.get("start_time") and s.get("end_time"))
            current_type = "阶段型" if is_stage else "ddl型"
            
            edit_type = st.radio("日程类型", ["ddl型", "阶段型"], index=0 if current_type == "ddl型" else 1, horizontal=True, label_visibility="collapsed")

            deadline_val = datetime.fromisoformat(s["deadline_date"]).date()
            start_val = datetime.fromisoformat(s["start_time"]).time() if s.get("start_time") else time(11, 0)
            end_val = datetime.fromisoformat(s["end_time"]).time() if s.get("end_time") else time(13, 0)
            prep_val = datetime.fromisoformat(s["prep_start"]).date() if s.get("prep_start") else None
            cat_index = cat_names.index(s["category"]) if s["category"] in cat_names else 0

            with st.form(f"edit_{s['id']}_{edit_type}"):
                f1, f2, f3 = st.columns([2, 2, 1])
                with f1:
                    new_cat = st.selectbox("类别", cat_names, index=cat_index)
                    new_dl = st.date_input("截止日期", value=deadline_val)
                with f2:
                    new_note = st.text_input("备注", value=s["note"] or "")
                    new_prep = st.date_input("开始准备日期", value=prep_val if prep_val else today_bj())
                with f3:
                    if edit_type == "阶段型":
                        new_start = st.time_input("开始时间", value=start_val)
                        new_end = st.time_input("结束时间", value=end_val)
                    else:
                        new_start, new_end = None, None
                
                new_tags = st.multiselect("标签", options=list(tag_map.keys()), default=s["tag_ids"], format_func=lambda tid: tag_map[tid])
                
                _, btn_col = st.columns([5, 1])
                with btn_col:
                    saved = st.form_submit_button("保存", use_container_width=True)

            if saved:
                if edit_type == "阶段型" and new_end <= new_start:
                    st.error("结束时间必须晚于开始时间")
                else:
                    updates = {"category": new_cat, "note": new_note, "deadline_date": str(new_dl), "prep_start": str(new_prep)}
                    if edit_type == "阶段型":
                        updates["start_time"] = datetime.combine(new_dl, new_start).isoformat()
                        updates["end_time"] = datetime.combine(new_dl, new_end).isoformat()
                    else:
                        updates["start_time"] = None
                        updates["end_time"] = None
                    update(s["id"], user.id, updates, tag_ids=new_tags)
                    st.session_state[edit_key] = False
                    st.rerun()
