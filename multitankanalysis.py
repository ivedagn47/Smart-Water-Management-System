import pandas as pd
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Constants
tank_capacity = 10000  # Liters
thing_speak_links = {
    'Tank 1': 'https://api.thingspeak.com/channels/CHANNEL_ID_1/feeds.csv?api_key=API_KEY_1',
    'Tank 2': 'https://api.thingspeak.com/channels/CHANNEL_ID_2/feeds.csv?api_key=API_KEY_2',
    'Tank 3': 'https://api.thingspeak.com/channels/CHANNEL_ID_3/feeds.csv?api_key=API_KEY_3'
}

def fetch_data(source, from_csv=False):
    if from_csv:
        return pd.read_csv(source)
    else:
        response = requests.get(source)
        return pd.read_csv(io.StringIO(response.text))

def preprocess(df):
    # Clean and standardize column names
    df.columns = df.columns.str.strip().str.lower()

    if "created_at" not in df.columns or "field1" not in df.columns:
        raise ValueError(f"Missing columns! Found columns: {list(df.columns)}")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce") + timedelta(hours=5, minutes=30)
    df = df.sort_values("created_at")
    df["field1"] = pd.to_numeric(df["field1"], errors="coerce").fillna(0)
    df["water_liters"] = (df["field1"] / 100) * tank_capacity
    df["water_liters"] = df["water_liters"].clip(0, tank_capacity)
    return df

def calculate_usage_metrics(df):
    df = df.copy()
    df["date"] = df["created_at"].dt.date
    df["hour"] = df["created_at"].dt.hour
    df["water_diff"] = df["water_liters"].diff()
    df["time_diff"] = df["created_at"].diff().dt.total_seconds()
    df["usage_rate"] = df["water_diff"] / df["time_diff"]
    return df

def summarize(df):
    summary = {}
    df = calculate_usage_metrics(df)

    # 1. Average Daily Consumption (Liters) — only positive usage
    daily = df.groupby("date")["water_diff"].sum()
    daily_filtered = daily[daily > 0]
    avg_consumption = round(daily_filtered.mean(), 2) if not daily_filtered.empty else 0

    # 2. Peak Usage Hour
    hourly = df.groupby("hour")["usage_rate"].mean()
    peak_hour = int(hourly.idxmax().item()) if not hourly.empty else "N/A"

    # 3. Average Refill Time (seconds)
    refills = df[df["water_diff"] > 0]
    avg_refill_time = round(refills["time_diff"].mean(), 2) if not refills.empty else "N/A"

    # # 4. Status Counts
    # df["status"] = df["water_diff"].apply(
    #     lambda x: 'Filling' if x > 0 else ('Draining' if x < 0 else 'Idle')
    # )
    # status_counts = df["status"].value_counts().to_dict()

    # 5. Weekly Summary (Liters)
    df["week"] = df["created_at"].dt.to_period("W").astype(str)
    weekly_summary = df.groupby("week")["water_diff"].sum().reset_index()

    # 6. Anomalies based on usage_rate deviation
    std_dev = df["usage_rate"].std()
    anomalies = df[abs(df["usage_rate"]) > std_dev * 2] if pd.notna(std_dev) and std_dev > 0 else pd.DataFrame()

    # 💡 Final formatted summary with UNITS
    formatted_summary = {
        "Average Daily Consumption": f"{avg_consumption} Liters",
        "Peak Usage Hour": f"{peak_hour} (24h format)",
        "Average Refill Time": f"{avg_refill_time} seconds" if avg_refill_time != "N/A" else "N/A",
        # "Time in Idle State": f"{status_counts.get('Idle', 0)} samples",
        # "Time in Draining State": f"{status_counts.get('Draining', 0)} samples",
        # "Time in Filling State": f"{status_counts.get('Filling', 0)} samples"
    }

    return formatted_summary, daily, hourly, weekly_summary, anomalies

def compare_tanks(data_dict):
    all_tanks = []
    for name, df in data_dict.items():
        df["Tank"] = name
        df = calculate_usage_metrics(df)
        all_tanks.append(df)
    return pd.concat(all_tanks, ignore_index=True)

def analyze_all_sources(sources, from_csv=False):
    data = {}
    summaries = {}
    daily_trends = {}
    hourly_usage = {}
    weekly_summary = {}
    anomalies_dict = {}

    for tank, source in sources.items():
        df = fetch_data(source, from_csv=from_csv)
        df = preprocess(df)
        summary, daily, hourly, weekly, anomalies = summarize(df)
        data[tank] = df
        summaries[tank] = summary
        daily_trends[tank] = daily
        hourly_usage[tank] = hourly
        weekly_summary[tank] = weekly
        anomalies_dict[tank] = anomalies

    comparison_df = compare_tanks(data)
    return {
        "data": data,
        "summaries": summaries,
        "daily": daily_trends,
        "hourly": hourly_usage,
        "weekly": weekly_summary,
        "anomalies": anomalies_dict,
        "comparison": comparison_df
    }
