import pandas as pd
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_all
from src.schedule.tags import fetch_tags

load_style()
user = require_login()

st.title("📊 统计")

data = fetch_all(user.id)
if not data:
    st.info("暂无数据")
    st.stop()

all_tags = fetch_tags(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}

# ========== 标签筛选 ==========
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
            key=f"stat_filter_{group_name}",
        )
        filter_ids.extend(chosen)

if filter_ids:
    data = [s for s in data if set(s.get("tag_ids", [])) & set(filter_ids)]

if not data:
    st.info("所选标签下无数据")
    st.stop()

df = pd.DataFrame(data)
df["deadline_date"] = pd.to_datetime(df["deadline_date"])

# ========== 未完成统计 ==========
pending = df[df["status"].isin(["pending", "overdue"])]
st.metric("未完成总数", len(pending))

if not pending.empty:
    st.subheader("未完成分类统计")
    st.bar_chart(pending["category"].value_counts())

# ========== 历史统计 ==========
st.subheader("历史统计")
c1, c2 = st.columns(2)
start = c1.date_input("起始日期（可空白）", value=None)
end = c2.date_input("结束日期（可空白）", value=None)

mask = pd.Series(True, index=df.index)
if start:
    mask &= df["deadline_date"] >= pd.Timestamp(start)
if end:
    mask &= df["deadline_date"] <= pd.Timestamp(end)
sub = df[mask]

if sub.empty:
    st.info("所选范围内无数据")
    st.stop()

freq = st.selectbox("统计粒度", ["按日", "按周", "按月", "按年"])
freq_map = {"按日": "D", "按周": "W", "按月": "ME", "按年": "YE"}

import altair as alt

grouped = sub.set_index("deadline_date").resample(freq_map[freq]).agg(
    截止数量=("id", "count"),
    完成数量=("status", lambda x: (x == "completed").sum())
).reset_index()

# 根据粒度决定横轴标签格式
if freq == "按日":
    grouped["日期"] = grouped["deadline_date"].dt.strftime("%m-%d")
elif freq == "按周":
    grouped["日期"] = grouped["deadline_date"].dt.strftime("%m-%d") + " 周"
elif freq == "按月":
    grouped["日期"] = grouped["deadline_date"].dt.strftime("%Y-%m")
else:  # 按年
    grouped["日期"] = grouped["deadline_date"].dt.strftime("%Y")

melted = grouped.melt(
    id_vars="日期",
    value_vars=["截止数量", "完成数量"],
    var_name="类型",
    value_name="数量"
)

chart = alt.Chart(melted).mark_bar(
    cornerRadiusTopLeft=4, 
    cornerRadiusTopRight=4
).encode(
    x=alt.X("日期:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelPadding=10, domain=False, ticks=False)),
    xOffset="类型:N",
    y=alt.Y("数量:Q", title=None, axis=alt.Axis(grid=True, gridColor="#F1F5F9", domain=False, ticks=False)),
    color=alt.Color(
        "类型:N",
        scale=alt.Scale(
            domain=["截止数量", "完成数量"],
            range=["#93C5FD", "#2563EB"]   # 高级浅蓝 / 高级深蓝
        ),
        legend=alt.Legend(
            title=None, 
            orient="top", 
            direction="horizontal",
            symbolType="circle",
            symbolSize=100
        )
    ),
    tooltip=["日期:N", "类型:N", "数量:Q"]
).properties(
    height=400
).configure_view(
    strokeOpacity=0
).configure_axis(
    labelFont="sans-serif",
    labelColor="#64748B",
    labelFontSize=12
)

st.altair_chart(chart, use_container_width=True)

st.divider()

# ========== 已完成历史任务表格 ==========
st.subheader("✅ 已完成任务列表")

# 从原始数据中筛出已完成的
completed_df = df[df["status"] == "completed"].copy()

if completed_df.empty:
    st.info("暂无已完成的任务")
else:
    # 提取所有出现过的类别供用户筛选
    all_categories = completed_df["category"].unique().tolist()
    
    # 类别筛选器（多选，默认全选）
    selected_cats = st.multiselect(
        "按类别筛选（可多选）",
        options=all_categories,
        default=all_categories
    )

    if not selected_cats:
        st.warning("请至少选择一个类别")
    else:
        # 应用筛选
        filtered_df = completed_df[completed_df["category"].isin(selected_cats)]
        
        # 提取要展示的列
        display_df = filtered_df[[
            "deadline_date", "category", "note", "prep_start", "tag_ids"
        ]].copy()
        
        # 建立快速查询字典，提高运行速度
        tag_dict = {t["id"]: (t["name"], t["group_name"]) for t in all_tags}
        
        def get_subject(tag_ids):
            if not tag_ids:
                return ""
            subjects = [tag_dict[tid][0] for tid in tag_ids if tid in tag_dict and tag_dict[tid][1] == "学科"]
            return "、".join(subjects)

        display_df["学科"] = display_df["tag_ids"].apply(get_subject)
        
        # 格式化日期
        display_df["deadline_date"] = pd.to_datetime(display_df["deadline_date"]).dt.strftime("%Y-%m-%d")
        display_df["prep_start"] = pd.to_datetime(display_df["prep_start"]).dt.strftime("%Y-%m-%d")
        display_df["prep_start"] = display_df["prep_start"].replace("NaT", "")
        display_df["note"] = display_df["note"].fillna("")
        
        # 调整列顺序并重命名
        display_df = display_df[["deadline_date", "category", "学科", "note", "prep_start"]]
        display_df.columns = ["截止日期", "类别", "学科", "备注", "开始准备日期"]
        
        # 按截止日期倒序排列
        display_df = display_df.sort_values("截止日期", ascending=False)

        # 构造 column_config 强制居中
        centered_config = {
            col: st.column_config.TextColumn(col, alignment="center") 
            for col in ["截止日期", "类别", "学科", "备注", "开始准备日期"]
        }
        
        # 注意：因为日期之前已经转成了字符串，所以用 TextColumn 即可
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            column_config=centered_config
        )
        st.caption(f"共 {len(display_df)} 条已完成任务")
