import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from multitankanalysis import analyze_all_sources

# Page config
st.set_page_config(page_title="Smart Water Management Dashboard", layout="wide")
st.title("🚰 Smart Water Management: Multi-Tank Analysis")

# Style
sns.set_style("darkgrid")
plt.rcParams.update({
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.edgecolor": "#00f5ff",
    "xtick.color": "#00f5ff",
    "ytick.color": "#00f5ff",
    "axes.labelcolor": "#00f5ff",
    "axes.titlecolor": "#00f5ff"
})

st.sidebar.header("Upload Data or Enter ThingSpeak Links")
csv_uploads = {}
use_csv = st.sidebar.toggle("Use CSV files instead of ThingSpeak links")

# Input Section
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

# ⏎ Enter Button
process_data = st.sidebar.button("✅ Enter and Analyze Data")

# Once the user clicks Enter and all 3 sources are given
if process_data and csv_uploads and len(csv_uploads) == 3:
    st.success("Data successfully loaded. Generating insights...")

    analysis = analyze_all_sources(csv_uploads, from_csv=use_csv)

    st.header("📊 Tank-wise Summary")
    for tank, summary in analysis['summaries'].items():
        st.subheader(f"{tank} Summary")
        # Add units to values where relevant
        readable_summary = {
            "Average Daily Consumption (Liters)": round(summary.get("average_daily_consumption", 0), 2),
            "Peak Usage Hour (0–23)": summary.get("peak_usage_hour"),
            "Average Refill Time (seconds)": round(summary.get("average_refill_time", 0), 2)
        }
        status_counts = summary.get("status_counts", {})
        for status, count in status_counts.items():
            readable_summary[f"Time in '{status}' State (samples)"] = count
        st.json(readable_summary)

    st.header("📈 Daily Consumption Trends (Liters)")
    for tank, daily in analysis['daily'].items():
        st.subheader(tank)
        fig, ax = plt.subplots()
        ax.plot(daily.index, daily.values, marker='o', color="#39ff14", label='Daily Usage')
        ax.set_xlabel("Date")
        ax.set_ylabel("Water Used (Liters)")
        ax.set_title(f"{tank} - Daily Consumption")
        ax.legend()
        st.pyplot(fig)

    st.header("⏱ Hourly Usage Patterns (Liters/Second)")
    for tank, hourly in analysis['hourly'].items():
        st.subheader(tank)
        fig, ax = plt.subplots()
        ax.bar(hourly.index, hourly.values, color="#f542f5")
        ax.set_xlabel("Hour of Day (0–23)")
        ax.set_ylabel("Average Usage Rate (L/s)")
        ax.set_title(f"{tank} - Hourly Usage Pattern")
        st.pyplot(fig)

    st.header("🗓 Weekly Summary (Liters)")
    for tank, week in analysis['weekly'].items():
        st.subheader(tank)
        st.dataframe(week.rename(columns={"water_diff": "Weekly Usage (Liters)"}))

    st.header("🚨 Detected Anomalies")
    for tank, df in analysis['anomalies'].items():
        st.subheader(tank)
        if df.empty:
            st.success("No anomalies detected.")
        else:
            st.dataframe(df[['created_at', 'water_liters', 'usage_rate']].rename(columns={
                "created_at": "Timestamp",
                "water_liters": "Water Level (Liters)",
                "usage_rate": "Usage Rate (L/s)"
            }).head(10))

    st.header("📊 Tank Comparison Overview")
    comp = analysis['comparison']
    if not comp.empty:
        st.subheader("Water Level Comparison Over Time (Liters)")
        fig, ax = plt.subplots()
        for name, group in comp.groupby("Tank"):
            ax.plot(group["created_at"], group["water_liters"], marker='o', label=name)
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Water Level (Liters)")
        ax.set_title("Tank Comparison")
        ax.legend()
        st.pyplot(fig)

else:
    st.info("Please upload or input data for all 3 tanks. 👉 Use the sidebar on the left!")

