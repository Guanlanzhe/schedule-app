import streamlit as st
from src.ui import load_style, require_login
from src.schedule.tags import fetch_tags, create_tag, delete_tag
from src.schedule.categories import (
    fetch_categories, create_category, delete_category
)

load_style()
user = require_login()

st.title("🏷️ 标签与类别管理")

# 成功提示
if st.session_state.pop("just_created_cat", False):
    st.success("✅ 已添加类别")
if st.session_state.pop("just_created_tag", False):
    st.success("✅ 已添加标签")

# 初始化两个计数器
if "cat_form_key" not in st.session_state:
    st.session_state["cat_form_key"] = 0
if "tag_form_key" not in st.session_state:
    st.session_state["tag_form_key"] = 0

# ========== 类别管理 ==========
st.subheader("类别")
with st.form(f"new_cat_{st.session_state['cat_form_key']}"):
    c1, c2 = st.columns([3, 1])
    cat_name = c1.text_input(
        "新类别名", placeholder="如：作业、考试、汇报",
        key=f"cat_input_{st.session_state['cat_form_key']}"
    )
    cat_submitted = c2.form_submit_button("添加类别")

if cat_submitted:
    if cat_name.strip():
        create_category(user.id, cat_name.strip())
        st.session_state["just_created_cat"] = True
        st.session_state["cat_form_key"] += 1
        st.rerun()
    else:
        st.warning("类别名不能为空")

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
with st.form(f"new_tag_{st.session_state['tag_form_key']}"):
    c1, c2 = st.columns(2)
    group_name = c1.text_input(
        "标签分类", placeholder="如：学科类、作业分类",
        key=f"tag_group_{st.session_state['tag_form_key']}"
    )
    name = c2.text_input(
        "标签名", placeholder="如：解剖、绘图作业",
        key=f"tag_name_{st.session_state['tag_form_key']}"
    )
    tag_submitted = st.form_submit_button("添加标签")

if tag_submitted:
    if group_name and name:
        create_tag(user.id, name.strip(), group_name.strip())
        st.session_state["just_created_tag"] = True
        st.session_state["tag_form_key"] += 1
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
