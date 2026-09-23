import streamlit as st
from src.ui import load_style, require_login
from src.schedule.tags import fetch_tags, create_tag, delete_tag

load_style()
user = require_login()

st.title("🏷️ 标签管理")

tags = fetch_tags(user.id)

# 新建标签
with st.form("new_tag"):
    c1, c2 = st.columns(2)
    group_name = c1.text_input("标签分类", placeholder="如：学科类、作业分类")
    name = c2.text_input("标签名", placeholder="如：解剖、绘图作业")
    if st.form_submit_button("添加标签"):
        if group_name and name:
            create_tag(user.id, name.strip(), group_name.strip())
            st.success(f"已添加 {group_name} / {name}")
            st.rerun()
        else:
            st.warning("分类和标签名都要填")

# 展示现有标签，按分类分组
if not tags:
    st.info("还没有标签，先在上方添加")
    st.stop()

groups = {}
for t in tags:
    groups.setdefault(t["group_name"], []).append(t)

for group_name, items in groups.items():
    st.subheader(group_name)
    cols = st.columns(4)
    for i, t in enumerate(items):
        with cols[i % 4]:
            if st.button(f"🗑️ {t['name']}", key=f"del_tag_{t['id']}",
                         help="点击删除该标签"):
                delete_tag(t["id"], user.id)
                st.rerun()
