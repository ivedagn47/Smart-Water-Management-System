import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO
from multitank_analysis import analyze_all_sources

# Set visual theme
sns.set_style("darkgrid")
plt.rcParams.update({
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.edgecolor": "#00f5ff",  # neon-ish cyan
    "xtick.color": "#00f5ff",
    "ytick.color": "#00f5ff",
    "axes.labelcolor": "#00f5ff",
    "axes.titlecolor": "#00f5ff"
})

st.title("💧 Multitank Water Usage Dashboard")

# Sidebar filters
st.sidebar.header("⚙️ Settings")
from_csv = st.sidebar.checkbox("Use CSV Upload", False)

# Date Range Filter
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

thing_speak_links = {
    'Tank 1': 'https://api.thingspeak.com/channels/CHANNEL_ID_1/feeds.csv?api_key=API_KEY_1',
    'Tank 2': 'https://api.thingspeak.com/channels/CHANNEL_ID_2/feeds.csv?api_key=API_KEY_2',
    'Tank 3': 'https://api.thingspeak.com/channels/CHANNEL_ID_3/feeds.csv?api_key=API_KEY_3'
}

sources = {}
if from_csv:
    for tank in thing_speak_links:
        uploaded = st.sidebar.file_uploader(f"Upload CSV for {tank}", type="csv")
        if uploaded:
            sources[tank] = uploaded
else:
    sources = thing_speak_links

if sources:
    result = analyze_all_sources(sources, from_csv=from_csv)

    def filter_by_date(df):
        mask = (df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)
        return df.loc[mask]

    st.header("📈 Tank-wise Daily Consumption")
    for tank, series in result["daily"].items():
        df_filtered = result["data"][tank]
        df_filtered = filter_by_date(df_filtered)
        daily = df_filtered.groupby(df_filtered["created_at"].dt.date)["water_liters"].sum()

        st.subheader(tank)
        fig, ax = plt.subplots()
        ax.plot(daily.index, daily.values, marker='o', color='#00ffff', markerfacecolor='#ff00ff', label="Daily Usage")
        ax.set_xlabel("Date")
        ax.set_ylabel("Water Used (Liters)")
        ax.set_title(f"{tank} - Daily Consumption")
        ax.legend()
        st.pyplot(fig)

        # Download daily report
        daily_csv = daily.reset_index().rename(columns={"index": "Date", "water_liters": "Usage (Liters)"})
        st.download_button(f"⬇️ Download Daily Report - {tank}", daily_csv.to_csv(index=False), file_name=f"{tank}_daily.csv")

    st.header("🕒 Hourly Usage Rates")
    for tank, hourly in result["hourly"].items():
        st.subheader(tank)
        fig, ax = plt.subplots()
        ax.bar(hourly.index, hourly.values, color="#39ff14")
        ax.set_xlabel("Hour of Day (0-23)")
        ax.set_ylabel("Usage Rate (Liters/sec)")
        ax.set_title(f"{tank} - Hourly Average Usage Rate")
        st.pyplot(fig)

    st.header("📅 Weekly Water Usage Summary")
    for tank, weekly in result["weekly"].items():
        st.subheader(tank)
        fig, ax = plt.subplots()
        ax.plot(weekly["week"], weekly["water_diff"], marker='s', color='#f5ff00', markerfacecolor='#00ffea')
        ax.set_xlabel("Week")
        ax.set_ylabel("Total Usage (Liters)")
        ax.set_title(f"{tank} - Weekly Summary")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Download weekly report
        st.download_button(f"⬇️ Download Weekly Report - {tank}", weekly.to_csv(index=False), file_name=f"{tank}_weekly.csv")

    st.header("🚨 Anomalies in Usage")
    for tank, anomalies in result["anomalies"].items():
        st.subheader(tank)
        if anomalies.empty:
            st.success("No anomalies detected.")
        else:
            filtered_anomalies = filter_by_date(anomalies)
            st.dataframe(filtered_anomalies[["created_at", "water_liters", "usage_rate"]])
            st.download_button(f"⬇️ Download Anomalies - {tank}",
                               filtered_anomalies.to_csv(index=False),
                               file_name=f"{tank}_anomalies.csv")

    st.header("📋 Summary Statistics")
    for tank, summary in result["summaries"].items():
        st.subheader(tank)
        st.json(summary)

    st.header("📊 Cross-Tank Comparison")
    comparison_df = result["comparison"]
    comparison_df = filter_by_date(comparison_df)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=comparison_df, x="created_at", y="water_liters", hue="Tank", marker='o', ax=ax)
    ax.set_title("Tank Water Levels Over Time")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Water (Liters)")
    st.pyplot(fig)

else:
    st.warning("Upload CSV or use ThingSpeak URLs to continue.")
