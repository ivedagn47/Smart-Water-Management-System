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

    # 1. Daily Consumption (Ignore negative values)
    daily = df.groupby("date")["water_diff"].sum()
    daily_filtered = daily[daily > 0]  # filter only valid positive usage
    summary["average_daily_consumption"] = round(daily_filtered.mean(), 2) if not daily_filtered.empty else 0

    # 2. Peak Hour
    hourly = df.groupby("hour")["usage_rate"].mean()
    if not hourly.empty and hourly.idxmax() is not None:
        summary["peak_usage_hour"] = int(hourly.idxmax().item())
    else:
        summary["peak_usage_hour"] = "N/A"

    # 3. Refill Time
    refills = df[df["water_diff"] > 0]
    if not refills.empty:
        summary["average_refill_time"] = round(refills["time_diff"].mean(), 2)
    else:
        summary["average_refill_time"] = "N/A"

    # 4. Tank Status Time Counts
    df["status"] = df["water_diff"].apply(lambda x: 'Filling' if x > 0 else ('Draining' if x < 0 else 'Idle'))
    summary["status_counts"] = df["status"].value_counts().to_dict()

    # 5. Weekly Summary
    df["week"] = df["created_at"].dt.to_period("W").astype(str)
    weekly_summary = df.groupby("week")["water_diff"].sum().reset_index()

    # 6. Anomalies (very high usage rate outliers)
    std_dev = df["usage_rate"].std()
    if pd.notna(std_dev) and std_dev > 0:
        anomalies = df[abs(df["usage_rate"]) > std_dev * 2]
    else:
        anomalies = pd.DataFrame(columns=df.columns)

    return summary, daily, hourly, weekly_summary, anomalies

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
