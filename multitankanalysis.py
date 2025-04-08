import pandas as pd
from datetime import datetime
import numpy as np

def clean_and_prepare(df):
    df = df.copy()
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.dropna(subset=['created_at'])

    if 'field1' in df.columns:
        df['water_liters'] = pd.to_numeric(df['field1'], errors='coerce')
    elif 'water_liters' in df.columns:
        df['water_liters'] = pd.to_numeric(df['water_liters'], errors='coerce')
    else:
        raise ValueError("Missing expected column for water data (field1 or water_liters)")

    df = df.dropna(subset=['water_liters'])
    df = df.sort_values('created_at')
    df = df[df['water_liters'] >= 0]
    return df[['created_at', 'water_liters']]

def summarize_data(df):
    stats = {
        'Total Readings': len(df),
        'Total Liters Recorded': round(df['water_liters'].sum(), 2),
        'Average Usage per Reading': round(df['water_liters'].diff().mean(), 2),
        'Maximum Recorded': df['water_liters'].max(),
        'Minimum Recorded': df['water_liters'].min(),
    }
    return stats

def detect_anomalies(df):
    df = df.copy()
    df['usage_rate'] = df['water_liters'].diff()
    threshold = df['usage_rate'].mean() + 3 * df['usage_rate'].std()
    anomalies = df[df['usage_rate'] > threshold]
    return anomalies

def group_by_hour(df):
    df = df.copy()
    df['hour'] = df['created_at'].dt.hour
    return df.groupby('hour')['water_liters'].mean()

def group_by_day(df):
    df = df.copy()
    df['date'] = df['created_at'].dt.date
    return df.groupby('date')['water_liters'].mean()

def weekly_summary(df):
    df = df.copy()
    df['week'] = df['created_at'].dt.to_period('W').astype(str)
    df['water_diff'] = df['water_liters'].diff()
    return df.groupby('week')[['water_diff']].sum().reset_index()

def analyze_all_sources(source_dict, from_csv=False):
    summaries = {}
    daily_trends = {}
    hourly_patterns = {}
    weekly_summaries = {}
    anomaly_data = {}
    all_combined = []

    for tank, source in source_dict.items():
        if from_csv:
            df = pd.read_csv(source)
        else:
            df = pd.read_csv(source)

        df = clean_and_prepare(df)

        summaries[tank] = summarize_data(df)
        daily_trends[tank] = group_by_day(df)
        hourly_patterns[tank] = group_by_hour(df)
        weekly_summaries[tank] = weekly_summary(df)
        anomaly_data[tank] = detect_anomalies(df)

        df['Tank'] = tank
        all_combined.append(df)

    comparison_df = pd.concat(all_combined)

    return {
        'summaries': summaries,
        'daily': daily_trends,
        'hourly': hourly_patterns,
        'weekly': weekly_summaries,
        'anomalies': anomaly_data,
        'comparison': comparison_df
    }
