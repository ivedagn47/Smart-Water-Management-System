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

if csv_uploads and len(csv_uploads) == 3:
    st.success("Data successfully loaded. Generating insights...")
    analysis = analyze_all_sources(csv_uploads, from_csv=use_csv)

    st.header("📊 Tank-wise Summary")
    for tank, summary in analysis['summaries'].items():
        # Format and add units to the summary
        summary["average_daily_consumption"] = f"{summary['average_daily_consumption']:.2f} liters/day"
        
        # Format peak_usage_hour to show AM or PM only
        hour = summary["peak_usage_hour"]
        hour = int(hour) % 12  # Convert to 12-hour format
        am_pm = "AM" if int(summary["peak_usage_hour"]) < 12 else "PM"
        summary["peak_usage_hour"] = f"{hour if hour != 0 else 12} {am_pm}"
        
        summary["average_refill_time"] = f"{summary['average_refill_time']:.2f} seconds"
        
        # Convert status event counts to hours
        if 'status_counts' in summary:
            status_hours = {}
            for status, count in summary['status_counts'].items():
                # Sum of time_diff for each status (in seconds)
                status_data = summary.get('status_data', {}).get(status, [])
                total_time = sum([entry['time_diff'] for entry in status_data]) / 3600  # Convert seconds to hours
                status_hours[status] = f"{total_time:.2f} hours"
            
            summary["status_counts"] = status_hours

        st.subheader(f"{tank} Summary")
        st.json(summary)

    st.header("📈 Daily Consumption Trends")
    for tank, daily in analysis['daily'].items():
        st.line_chart(daily, use_container_width=True)
        st.write("### Daily Consumption (liters/day)")
        st.write("Time (Days) vs Water Consumption (liters)")

    st.header("⏱ Hourly Usage Patterns")
    for tank, hourly in analysis['hourly'].items():
        st.bar_chart(hourly, use_container_width=True)
        st.write("### Hourly Usage Patterns")
        st.write("Time (Hours) vs Usage Rate (liters/hour)")

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
        st.line_chart(
            comp.pivot(index="created_at", columns="Tank", values="water_liters"),
            use_container_width=True,
        )
        st.write("### Tank Comparison Overview")
        st.write("Time (Days) vs Water Levels (liters)")

else:
    st.warning("Please upload or input data for all 3 tanks. 👉 Use the sidebar on the left!")
