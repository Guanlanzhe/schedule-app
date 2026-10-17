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

# 渲染药丸样式的辅助函数
def render_pills(items, on_delete):
    """渲染一排带删除功能的药丸"""
    if not items:
        st.caption("暂无数据")
        return
    
    # 用 HTML 组合出一排药丸
    html = "<div style='display: flex; flex-wrap: wrap; gap: 8px;'>"
    for item in items:
        html += f"""
        <div style='background-color: #EFF6FF; color: #2563EB; padding: 4px 12px; border-radius: 999px; font-size: 0.9rem; display: inline-flex; align-items: center;'>
            {item['name']}
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    
    # 因为纯 HTML 里的按钮没法触发 Streamlit 回调，
    # 所以我们在下面放一行小小的原生按钮来执行删除（或者用折叠框）。
    # 为了美观，这里我们用列来排版小巧的删除按钮。
    pass

# ========== 类别管理 ==========
with st.container(border=True):
    st.markdown("### 类别管理")
    st.caption("类别用于大类的划分，如“作业”、“考试”")
    
    # 添加表单
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
    
    # 展示已有类别
    cats = fetch_categories(user.id)
    if cats:
        # 使用多列来展示带删除按钮的小标签
        cols = st.columns(5)
        for i, c in enumerate(cats):
            with cols[i % 5]:
                # 原生按钮最稳妥的展示方式
                if st.button(f"❌ {c['name']}", key=f"del_cat_{c['id']}", use_container_width=True):
                    delete_category(c["id"], user.id)
                    st.rerun()

st.write("")

# ========== 标签管理 ==========
with st.container(border=True):
    st.markdown("### 标签管理")
    st.caption("标签提供更细维度的筛选，如“学科”下的“解剖”")
    
    # 添加表单
    with st.form(f"new_tag_{st.session_state['tag_form_key']}"):
        c1, c2, c3 = st.columns([2, 2, 1])
        group_name = c1.text_input(
            "标签分类", placeholder="如：学科、作业类型",
            key=f"tag_group_{st.session_state['tag_form_key']}"
        )
        name = c2.text_input(
            "标签名", placeholder="如：解剖、绘图",
            key=f"tag_name_{st.session_state['tag_form_key']}"
        )
        tag_submitted = c3.form_submit_button("添加", use_container_width=True)

    if tag_submitted:
        if group_name and name:
            create_tag(user.id, name.strip(), group_name.strip())
            st.session_state["just_created_tag"] = True
            st.session_state["tag_form_key"] += 1
            st.rerun()
        else:
            st.warning("分类和标签名都要填")

    st.write("")

    # 展示已有标签
    tags = fetch_tags(user.id)
    if not tags:
        st.caption("暂无标签")
    else:
        groups = {}
        for t in tags:
            groups.setdefault(t["group_name"], []).append(t)

        for group_name, items in groups.items():
            st.markdown(f"**{group_name}**")
            # 使用多列来展示标签的删除按钮
            cols = st.columns(4)
            for i, t in enumerate(items):
                with cols[i % 4]:
                    if st.button(f"❌ {t['name']}", key=f"del_tag_{t['id']}", use_container_width=True):
                        delete_tag(t["id"], user.id)
                        st.rerun()
            st.write("") # 每个组之间留空
