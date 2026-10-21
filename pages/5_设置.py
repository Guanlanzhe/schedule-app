import streamlit as st
from src.ui import load_style, require_login
from src.schedule.tags import fetch_tags, create_tag, delete_tag
from src.schedule.categories import (
    fetch_categories, create_category, delete_category
)

load_style()
user = require_login()

st.title("标签与设置")
st.write("")

# 成功提示
if st.session_state.pop("just_created_cat", False):
    st.toast("✅ 已添加类别")
if st.session_state.pop("just_created_tag", False):
    st.toast("✅ 已添加标签")

# 初始化计数器
if "cat_form_key" not in st.session_state:
    st.session_state["cat_form_key"] = 0
if "tag_form_key" not in st.session_state:
    st.session_state["tag_form_key"] = 0

# ========== 类别管理 ==========
with st.container(border=True):
    st.markdown("### 类别管理")
    st.caption("类别用于大类的划分，如“作业”、“考试”")
    
    with st.form(f"new_cat_{st.session_state['cat_form_key']}"):
        c1, c2 = st.columns([4, 1])
        cat_name = c1.text_input(
            "新类别名", placeholder="输入新类别后点击右侧按钮", label_visibility="collapsed",
            key=f"cat_input_{st.session_state['cat_form_key']}"
        )
        cat_submitted = c2.form_submit_button("添加", use_container_width=True)

    if cat_submitted:
        if cat_name.strip():
            create_category(user.id, cat_name.strip())
            st.session_state["just_created_cat"] = True
            st.session_state["cat_form_key"] += 1
            st.rerun()
        else:
            st.warning("类别名不能为空")

    st.write("")
    
    cats = fetch_categories(user.id)
    if cats:
        cols = st.columns(5)
        for i, c in enumerate(cats):
            with cols[i % 5]:
                if st.button(f"❌ {c['name']}", key=f"del_cat_{c['id']}", use_container_width=True):
                    delete_category(c["id"], user.id)
                    st.rerun()

st.write("")

# ========== 标签管理 ==========
with st.container(border=True):
    st.markdown("### 标签管理")
    st.caption("标签提供更细维度的筛选。先选择左边的“标签分类”，再输入右边的“标签名”。")
    
    tags = fetch_tags(user.id)
    existing_groups = list(set([t["group_name"] for t in tags])) if tags else []
    
    # 提供两种选项：从已有分类选，或者新建分类
    group_options = existing_groups + ["➕ 新建分类..."]
    
    with st.form(f"new_tag_{st.session_state['tag_form_key']}"):
        c1, c2, c3 = st.columns([2, 2, 1])
        
        # 如果是第一次用，没有已有分类，默认就显示新建
        selected_group = c1.selectbox(
            "标签分类", 
            options=group_options,
            key=f"tag_group_select_{st.session_state['tag_form_key']}"
        )
        
        # 如果选了“新建分类”，则弹出一个输入框
        if selected_group == "➕ 新建分类...":
            group_name = c1.text_input(
                "输入新分类名", placeholder="如：学科、作业类型",
                key=f"tag_group_input_{st.session_state['tag_form_key']}"
            )
        else:
            group_name = selected_group
            
        name = c2.text_input(
            "标签名", placeholder="如：解剖、绘图",
            key=f"tag_name_{st.session_state['tag_form_key']}"
        )
        tag_submitted = c3.form_submit_button("添加标签", use_container_width=True)

    if tag_submitted:
        if group_name and name.strip():
            create_tag(user.id, name.strip(), group_name.strip())
            st.session_state["just_created_tag"] = True
            st.session_state["tag_form_key"] += 1
            st.rerun()
        else:
            st.warning("请确保已填写（或选择）了标签分类，并输入了标签名")

    st.write("")
    st.divider()

    # 展示已有标签 (使用 HTML 药丸样式，更节省空间)
    if not tags:
        st.caption("暂无标签")
    else:
        groups = {}
        for t in tags:
            groups.setdefault(t["group_name"], []).append(t)

        for group_name, items in groups.items():
            st.markdown(f"**{group_name}**")
            
            # 使用原生按钮渲染，保持整洁
            cols = st.columns(5)
            for i, t in enumerate(items):
                with cols[i % 5]:
                    if st.button(f"❌ {t['name']}", key=f"del_tag_{t['id']}", use_container_width=True):
                        delete_tag(t["id"], user.id)
                        st.rerun()
            st.write("")
