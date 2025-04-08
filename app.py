import streamlit as st
import pandas as pd
from multi_tank_analysis import analyze_all_sources

st.set_page_config(page_title="Smart Water Management Dashboard", layout="wide")
st.title("🚰 Smart Water Management: Multi-Tank Analysis")

st.sidebar.header("Upload Data or Enter ThingSpeak Links")

csv_uploads = {}
use_csv = st.sidebar.toggle("Use CSV files instead of ThingSpeak links")

for i in range(1, 4):
    tank_key = f"Tank {i}"
    if use_csv:
        uploaded = st.sidebar.file_uploader(f"Upload CSV for {tank_key}", type="csv")
        if uploaded:
            csv_uploads[tank_key] = uploaded
    else:
        link = st.sidebar.text_input(f"ThingSpeak Link for {tank_key}", key=tank_key)
        if link:
            csv_uploads[tank_key] = link

if csv_uploads and len(csv_uploads) == 3:
    st.success("Data successfully loaded. Generating insights...")
    analysis = analyze_all_sources(csv_uploads, from_csv=use_csv)

    st.header("📊 Tank-wise Summary")
    for tank, summary in analysis['summaries'].items():
        st.subheader(f"{tank} Summary")
        st.json(summary)

    st.header("📈 Daily Consumption Trends")
    for tank, daily in analysis['daily'].items():
        st.subheader(f"📅 {tank} Daily Trend")
        st.line_chart(daily, use_container_width=True)

    st.header("⏱️ Hourly Usage Patterns")
    for tank, hourly in analysis['hourly'].items():
        st.subheader(f"🕒 {tank} Hourly Usage")
        st.bar_chart(hourly, use_container_width=True)

    st.header("🗓️ Weekly Summary")
    weekly_data = []
    for tank, week in analysis['weekly'].items():
        st.subheader(f"📅 {tank} Weekly Summary")

        # Highlight negative values in red and style the table
        def highlight_neg(val):
            return 'color: red;' if isinstance(val, (int, float)) and val < 0 else ''

        styled_week = week.style.applymap(highlight_neg, subset=['water_diff'])
        st.dataframe(styled_week, use_container_width=True)

        week_copy = week.copy()
        week_copy['Tank'] = tank
        weekly_data.append(week_copy)

    # Combined weekly usage comparison
    if weekly_data:
        st.subheader("📉 Total Weekly Usage Comparison")
        combined_week = pd.concat(weekly_data)
        combined_week_chart = combined_week.pivot(index="week", columns="Tank", values="water_diff")
        st.line_chart(combined_week_chart, use_container_width=True)

    st.header("🚨 Detected Anomalies")
    for tank, df in analysis['anomalies'].items():
        st.subheader(f"⚠️ {tank} Anomalies")
        st.dataframe(df[['created_at', 'water_liters', 'usage_rate']].head(10), use_container_width=True)

    st.header("📊 Tank Comparison Overview")
    comp = analysis['comparison']
    if not comp.empty:
        st.line_chart(
            comp.pivot(index="created_at", columns="Tank", values="water_liters"),
            use_container_width=True
        )
else:
    st.warning("Please upload or input data for all 3 tanks. 👉 Use the sidebar on the left!")


