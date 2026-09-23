import pandas as pd
import streamlit as st
from src.ui import load_style, require_login
from src.schedule.db import fetch_all

load_style()
user = require_login()

st.title("📊 统计")

data = fetch_all(user.id)
if not data:
    st.info("暂无数据")
    st.stop()

df = pd.DataFrame(data)
df["deadline_date"] = pd.to_datetime(df["deadline_date"])

# 未完成总数 + 分类
pending = df[df["status"].isin(["pending", "overdue"])]
st.metric("未完成总数", len(pending))

if not pending.empty:
    st.subheader("未完成分类统计")
    st.bar_chart(pending["category"].value_counts())

# 历史统计
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

grouped = sub.set_index("deadline_date").resample(freq_map[freq]).agg(
    截止数量=("id", "count"),
    完成数量=("status", lambda x: (x == "completed").sum())
)
st.bar_chart(grouped)