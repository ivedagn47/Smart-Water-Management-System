import pandas as pd
import requests
from datetime import datetime, timedelta
import io

tank_capacity = 10000  # Liters

def fetch_data(source, from_csv=False):
    if from_csv:
        return pd.read_csv(source, encoding='utf-8-sig')
    else:
        response = requests.get(source)
        return pd.read_csv(io.StringIO(response.text), encoding='utf-8-sig')

def preprocess(df):
    df.columns = df.columns.str.strip().str.lower()

    if "created_at" not in df.columns or "field1" not in df.columns:
        raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")

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

def summarize_only_metrics(df):
    df = calculate_usage_metrics(df)

    daily = df.groupby("date")["water_diff"].sum()
    hourly = df.groupby("hour")["usage_rate"].mean()
    df["week"] = df["created_at"].dt.to_period("W").astype(str)
    weekly_summary = df.groupby("week")["water_diff"].sum().reset_index()

    std_dev = df["usage_rate"].std()
    anomalies = df[abs(df["usage_rate"]) > std_dev * 2] if pd.notna(std_dev) and std_dev > 0 else pd.DataFrame()

    return daily, hourly, weekly_summary, anomalies

def compare_tanks(data_dict):
    all_tanks = []
    for name, df in data_dict.items():
        df["Tank"] = name
        df = calculate_usage_metrics(df)
        all_tanks.append(df)
    return pd.concat(all_tanks, ignore_index=True)

def analyze_all_sources(sources, from_csv=False):
    data = {}
    daily_trends = {}
    hourly_usage = {}
    weekly_summary = {}
    anomalies_dict = {}

    for tank, source in sources.items():
        df = fetch_data(source, from_csv=from_csv)
        print(f"[DEBUG] Raw columns for {tank}: {df.columns.tolist()}")
        df = preprocess(df)
        daily, hourly, weekly, anomalies = summarize_only_metrics(df)
        data[tank] = df
        daily_trends[tank] = daily
        hourly_usage[tank] = hourly
        weekly_summary[tank] = weekly
        anomalies_dict[tank] = anomalies

    comparison_df = compare_tanks(data)
    return {
        "data": data,
        "daily": daily_trends,
        "hourly": hourly_usage,
        "weekly": weekly_summary,
        "anomalies": anomalies_dict,
        "comparison": comparison_df_
