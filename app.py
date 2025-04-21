import streamlit as st
import pandas as pd
from multitankanalysis import analyze_all_sources

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

# Button to trigger analysis after uploading all data
# if len(csv_uploads) == 3:
#     st.sidebar.button("Generate Insights", key="generate_insights")

if csv_uploads and len(csv_uploads) == 3 and st.sidebar.session_state.get("generate_insights"):
    st.success("Data successfully loaded. Generating insights...")
    analysis = analyze_all_sources(csv_uploads, from_csv=use_csv)

    st.header("📊 Tank-wise Summary")
    for tank, summary in analysis['summaries'].items():
        # Change "peak_usage_hour" to 6AM in tank summary
        summary["peak_usage_hour"] = "6AM"
        st.subheader(f"{tank} Summary")
        st.json(summary)

    st.header("📈 Daily Consumption Trends")
    for tank, daily in analysis['daily'].items():
        st.line_chart(daily, use_container_width=True)

    st.header("⏱ Hourly Usage Patterns")
    for tank, hourly in analysis['hourly'].items():
        st.bar_chart(hourly, use_container_width=True)

    st.header("🗓 Weekly Summary")
    for tank, week in analysis['weekly'].items():
        st.dataframe(week)

    st.header("🚨 Detected Anomalies")
    for tank, df in analysis['anomalies'].items():
        st.subheader(f"{tank}")
        st.dataframe(df[['created_at', 'water_liters', 'usage_rate']].head(10))

    st.header("📊 Tank Comparison Overview")
    comp = analysis['comparison']
    if not comp.empty:
        # Change pointers to neon colors
        st.line_chart(
            comp.pivot(index="created_at", columns="Tank", values="water_liters"),
            use_container_width=True,
            color=["#39FF14", "#00FFFF", "#FF1493"]  # Neon colors
        )
else:
    st.warning("Please upload or input data for all 3 tanks. 👉 Use the sidebar on the left!")
