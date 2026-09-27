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

freq = st.selectbox("统计粒度", ["按日", "按周", "按年"])
freq_map = {"按日": "D", "按周": "W", "按年": "Y"}

import altair as alt

grouped = sub.set_index("deadline_date").resample(freq_map[freq]).agg(
    截止数量=("id", "count"),
    完成数量=("status", lambda x: (x == "completed").sum())
).reset_index()

# 转成"长表"格式，Altair 分组柱状图需要
melted = grouped.melt(
    id_vars="deadline_date",
    value_vars=["截止数量", "完成数量"],
    var_name="类型",
    value_name="数量"
)

chart = alt.Chart(melted).mark_bar().encode(
    x=alt.X("deadline_date:T", title="日期", axis=alt.Axis(format="%m-%d")),
    xOffset="类型:N",              # 关键：让两根柱子并排
    y=alt.Y("数量:Q", title="数量"),
    color=alt.Color(
        "类型:N",
        scale=alt.Scale(
            domain=["截止数量", "完成数量"],
            range=["#7EB6E8", "#1F4E79"]   # 浅蓝=截止，深蓝=完成
        ),
        legend=alt.Legend(title=None)
    ),
    tooltip=["deadline_date:T", "类型:N", "数量:Q"]
).properties(height=400)

st.altair_chart(chart, use_container_width=True)
