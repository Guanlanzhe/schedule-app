import pandas as pd
import streamlit as st
import altair as alt
from src.ui import load_style, require_login
from src.schedule.db import fetch_all
from src.schedule.tags import fetch_tags

load_style()
user = require_login()

# ========== 注入 CSS：强制表格表头居中 ==========
st.markdown("""
<style>
    /* 强制 dataframe 表头文字居中 */
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("数据统计")
st.write("")

data = fetch_all(user.id)
if not data:
    st.info("暂无数据")
    st.stop()

all_tags = fetch_tags(user.id)
tag_map = {t["id"]: t["name"] for t in all_tags}

# ========== 1. 全局筛选器（折叠） ==========
with st.expander("🔍 筛选标签", expanded=False):
    filter_ids = []
    if all_tags:
        groups = {}
        for t in all_tags:
            groups.setdefault(t["group_name"], []).append(t)
        
        cols = st.columns(len(groups) if len(groups) > 0 else 1)
        for i, (group_name, items) in enumerate(groups.items()):
            with cols[i % len(groups)]:
                chosen = st.multiselect(
                    f"{group_name}",
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

# ========== 2. 未完成统计 (卡片化) ==========
pending = df[df["status"].isin(["pending", "overdue"])]
pending_count = len(pending)

st.markdown(f"""
<div style='background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
    <div style='color: #64748B; font-size: 0.9rem; font-weight: 500; margin-bottom: 0.5rem;'>当前未完成总数</div>
    <div style='color: #2563EB; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{pending_count}</div>
</div>
""", unsafe_allow_html=True)

if not pending.empty:
    with st.container(border=True):
        st.markdown("### 未完成分类占比")
        
        # 计算分类数量
        cat_counts = pending["category"].value_counts()
        
        # 用 HTML 渲染横向进度条
        for cat, count in cat_counts.items():
            percentage = (count / pending_count) * 100
            st.markdown(f"""
            <div style='margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 4px;'>
                    <span style='font-weight: 500; color: #334155;'>{cat}</span>
                    <span style='color: #64748B;'>{count} 项</span>
                </div>
                <div style='width: 100%; background-color: #F1F5F9; border-radius: 999px; height: 8px;'>
                    <div style='width: {percentage}%; background-color: #3B82F6; border-radius: 999px; height: 8px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.write("")

# ========== 3. 历史统计 (图表) ==========
with st.container(border=True):
    st.markdown("### 历史截止与完成趋势")
    
    c1, c2, c3 = st.columns(3)
    start = c1.date_input("起始日期（可空白）", value=None)
    end = c2.date_input("结束日期（可空白）", value=None)
    freq = c3.selectbox("统计粒度", ["按日", "按周", "按月", "按年"])

    mask = pd.Series(True, index=df.index)
    if start:
        mask &= df["deadline_date"] >= pd.Timestamp(start)
    if end:
        mask &= df["deadline_date"] <= pd.Timestamp(end)
    sub = df[mask]

    if sub.empty:
        st.info("所选范围内无数据")
    else:
        freq_map = {"按日": "D", "按周": "W", "按月": "ME", "按年": "YE"}
        
        grouped = sub.set_index("deadline_date").resample(freq_map[freq]).agg(
            截止数量=("id", "count"),
            完成数量=("status", lambda x: (x == "completed").sum())
        ).reset_index()

        # 横轴标签格式化
        if freq == "按日":
            grouped["日期"] = grouped["deadline_date"].dt.strftime("%m-%d")
        elif freq == "按周":
            grouped["日期"] = grouped["deadline_date"].dt.strftime("%m-%d") + " 周"
        elif freq == "按月":
            grouped["日期"] = grouped["deadline_date"].dt.strftime("%Y-%m")
        else:
            grouped["日期"] = grouped["deadline_date"].dt.strftime("%Y")

        melted = grouped.melt(
            id_vars="日期",
            value_vars=["截止数量", "完成数量"],
            var_name="类型",
            value_name="数量"
        )

        # 高级图表配置
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
                    range=["#93C5FD", "#2563EB"]
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
            height=350
        ).configure_view(
            strokeOpacity=0
        ).configure_axis(
            labelFont="sans-serif",
            labelColor="#64748B",
            labelFontSize=12
        )

        st.altair_chart(chart, use_container_width=True)

st.write("")

# ========== 4. 已完成任务列表 (表格) ==========
with st.container(border=True):
    st.markdown("### 已完成任务记录")
    
    # 从原始数据中筛出已完成的
    completed_df = df[df["status"] == "completed"].copy()

    if completed_df.empty:
        st.caption("暂无已完成的任务")
    else:
        # 类别筛选器放入折叠框
        with st.expander("🔍 筛选类别", expanded=False):
            all_categories = completed_df["category"].unique().tolist()
            selected_cats = st.multiselect(
                "选择类别",
                options=all_categories,
                default=all_categories
            )

        if not selected_cats:
            st.warning("请至少选择一个类别")
        else:
            filtered_df = completed_df[completed_df["category"].isin(selected_cats)]
            display_df = filtered_df[["deadline_date", "category", "note", "prep_start", "tag_ids"]].copy()
            
            tag_dict = {t["id"]: (t["name"], t["group_name"]) for t in all_tags}
            
            def get_subject(tag_ids):
                if not tag_ids:
                    return ""
                subjects = [tag_dict[tid][0] for tid in tag_ids if tid in tag_dict and tag_dict[tid][1] == "学科"]
                return "、".join(subjects)

            display_df["学科"] = display_df["tag_ids"].apply(get_subject)
            
            display_df["deadline_date"] = pd.to_datetime(display_df["deadline_date"]).dt.strftime("%Y-%m-%d")
            display_df["prep_start"] = pd.to_datetime(display_df["prep_start"]).dt.strftime("%Y-%m-%d")
            display_df["prep_start"] = display_df["prep_start"].replace("NaT", "")
            display_df["note"] = display_df["note"].fillna("")
            
            display_df = display_df[["deadline_date", "category", "学科", "note", "prep_start"]]
            display_df.columns = ["截止日期", "类别", "学科", "备注", "开始准备日期"]
            display_df = display_df.sort_values("截止日期", ascending=False)

            # 手动构建 HTML 表格，实现完美居中与高级质感
            html_table = """
            <div style='overflow-x: auto;'>
                <table style='width: 100%; border-collapse: collapse; text-align: center; font-size: 0.9rem; color: #334155;'>
                    <thead>
                        <tr style='background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;'>
                            <th style='padding: 12px; font-weight: 600; color: #475569;'>截止日期</th>
                            <th style='padding: 12px; font-weight: 600; color: #475569;'>类别</th>
                            <th style='padding: 12px; font-weight: 600; color: #475569;'>学科</th>
                            <th style='padding: 12px; font-weight: 600; color: #475569;'>备注</th>
                            <th style='padding: 12px; font-weight: 600; color: #475569;'>开始准备日期</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for index, row in display_df.iterrows():
                # 隔行变色，增加阅读体验
                bg_color = "#FFFFFF" if index % 2 == 0 else "#F8FAFC"
                html_table += f"""
                        <tr style='background-color: {bg_color}; border-bottom: 1px solid #E2E8F0;'>
                            <td style='padding: 10px;'>{row['截止日期']}</td>
                            <td style='padding: 10px;'>{row['类别']}</td>
                            <td style='padding: 10px;'>{row['学科']}</td>
                            <td style='padding: 10px;'>{row['备注']}</td>
                            <td style='padding: 10px;'>{row['开始准备日期']}</td>
                        </tr>
                """
            
            html_table += """
                    </tbody>
                </table>
            </div>
            """
            
            # 渲染 HTML 表格
            st.markdown(html_table, unsafe_allow_html=True)
            st.caption(f"共 {len(display_df)} 条记录")
