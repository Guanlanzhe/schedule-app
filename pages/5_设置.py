import streamlit as st
from src.ui import load_style, require_login
from src.schedule.tags import fetch_tags, create_tag, delete_tag
from src.schedule.categories import (
    fetch_categories, create_category, delete_category
)

load_style()
user = require_login()

st.title("🏷️ 标签与类别管理")

# ========== 类别管理 ==========
st.subheader("类别")
with st.form("new_cat"):
    c1, c2 = st.columns([3, 1])
    cat_name = c1.text_input("新类别名", placeholder="如：作业、考试、汇报")
    if c2.form_submit_button("添加类别"):
        if cat_name.strip():
            create_category(user.id, cat_name.strip())
            st.rerun()

cats = fetch_categories(user.id)
if cats:
    cols = st.columns(5)
    for i, c in enumerate(cats):
        with cols[i % 5]:
            if st.button(f"🗑️ {c['name']}", key=f"del_cat_{c['id']}",
                         help="点击删除该类别"):
                delete_category(c["id"], user.id)
                st.rerun()
else:
    st.caption("还没有类别")

st.divider()

# ========== 标签管理 ==========
st.subheader("标签")
with st.form("new_tag"):
    c1, c2 = st.columns(2)
    group_name = c1.text_input("标签分类", placeholder="如：学科类、作业分类")
    name = c2.text_input("标签名", placeholder="如：解剖、绘图作业")
    if st.form_submit_button("添加标签"):
        if group_name and name:
            create_tag(user.id, name.strip(), group_name.strip())
            st.rerun()
        else:
            st.warning("分类和标签名都要填")

tags = fetch_tags(user.id)
if not tags:
    st.caption("还没有标签")
    st.stop()

groups = {}
for t in tags:
    groups.setdefault(t["group_name"], []).append(t)

for group_name, items in groups.items():
    st.caption(group_name)
    cols = st.columns(4)
    for i, t in enumerate(items):
        with cols[i % 4]:
            if st.button(f"🗑️ {t['name']}", key=f"del_tag_{t['id']}",
                         help="点击删除该标签"):
                delete_tag(t["id"], user.id)
                st.rerun()
