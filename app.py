import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from multitankanalysis import analyze_all_sources

# Set page configuration
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
        # Plotting with a classy and clean style
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(daily.index, daily.values, label="Water Consumption (liters)", color="#1f77b4", lw=2)
        ax.set_xlabel('Time (Days)', fontsize=12)
        ax.set_ylabel('Water Consumption (Liters)', fontsize=12)
        ax.set_title(f"Daily Consumption Trends for {tank}", fontsize=14, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc="upper left", fontsize=10)
        st.pyplot(fig)

    st.header("⏱ Hourly Usage Patterns")
    for tank, hourly in analysis['hourly'].items():
        # Plotting with a more refined color palette and style
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(hourly.index, hourly.values, label="Usage Rate (liters)", color="#ff7f0e", alpha=0.8)
        ax.set_xlabel('Time (Hours)', fontsize=12)
        ax.set_ylabel('Usage Rate (Liters)', fontsize=12)
        ax.set_title(f"Hourly Usage Patterns for {tank}", fontsize=14, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc="upper right", fontsize=10)
        st.pyplot(fig)

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
        # Plotting comparison with more elegant colors
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = cm.viridis([0.1, 0.3, 0.7])  # Using a professional colormap
        for idx, tank in enumerate(comp['Tank'].unique()):
            tank_data = comp[comp['Tank'] == tank]
            ax.plot(tank_data['created_at'], tank_data['water_liters'], label=f"{tank}", color=colors[idx % len(colors)], lw=2)
        ax.set_xlabel('Time (Days)', fontsize=12)
        ax.set_ylabel('Water Levels (liters)', fontsize=12)
        ax.set_title("Tank Comparison Overview", fontsize=14, fontweight='bold')
        ax.legend(loc="upper left", fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)

else:
    st.warning("Please upload or input data for all 3 tanks. 👉 Use the sidebar on the left!")
