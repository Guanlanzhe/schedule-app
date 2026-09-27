import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta
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
# 东八区
BJ = timezone(timedelta(hours=8))

# 截止时间：ddl型用 deadline_date，阶段型用 start_time
def get_deadline(row):
    if row.get("start_time"):
        return pd.to_datetime(row["start_time"]).tz_convert(BJ).date()
    return pd.to_datetime(row["deadline_date"]).date()

df["deadline_dt"] = df.apply(
    lambda r: pd.Timestamp(get_deadline(r)), axis=1
)

# 完成时间：只有 completed 且有 completed_at 的才算
def get_completed_date(row):
    if row["status"] == "completed" and row.get("completed_at"):
        return pd.to_datetime(row["completed_at"]).tz_convert(BJ).date()
    return None

df["completed_dt"] = df.apply(
    lambda r: pd.Timestamp(get_completed_date(r)) if get_completed_date(r) else pd.NaT,
    axis=1
)

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

# 按截止日期筛选范围
mask = pd.Series(True, index=df.index)
if start:
    mask &= df["deadline_dt"] >= pd.Timestamp(start)
if end:
    mask &= df["deadline_dt"] <= pd.Timestamp(end)
sub = df[mask].copy()

if sub.empty:
    st.info("所选范围内无数据")
    st.stop()

freq = st.selectbox("统计粒度", ["按日", "按周", "按年"])
freq_map = {"按日": "D", "按周": "W", "按年": "Y"}
freq_code = freq_map[freq]

# ---- 截止数量：按 deadline_dt 分组 ----
deadline_counts = (
    sub.groupby(pd.Grouper(key="deadline_dt", freq=freq_code))
    .size()
    .rename("截止数量")
)

# ---- 完成数量：按 completed_dt 分组（只统计完成的） ----
completed_df = sub[sub["completed_dt"].notna()]
completed_counts = (
    completed_df.groupby(pd.Grouper(key="completed_dt", freq=freq_code))
    .size()
    .rename("完成数量")
)

# ---- 逾期数量：截至该时间点，累计截止 - 累计完成 ----
# 先把两个序列对齐到同一时间轴
all_index = deadline_counts.index.union(completed_counts.index).sort_values()
deadline_cum = deadline_counts.reindex(all_index, fill_value=0).cumsum()
completed_cum = completed_counts.reindex(all_index, fill_value=0).cumsum()
overdue_cum = (deadline_cum - completed_cum).clip(lower=0).rename("逾期数量")

# 合并成一张表，三根柱子并排
chart_df = pd.concat(
    [deadline_counts, completed_counts, overdue_cum],
    axis=1
).fillna(0)

# 保证顺序是 截止、完成、逾期
chart_df = chart_df[["截止数量", "完成数量", "逾期数量"]]

st.bar_chart(chart_df, stack=False)
