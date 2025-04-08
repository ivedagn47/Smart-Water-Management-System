import pandas as pd

def analyze_all_sources(sources: dict, from_csv: bool = False):
    summaries = {}
    daily = {}
    hourly = {}
    weekly = {}
    anomalies = {}
    comparison_data = []

    for tank, source in sources.items():
        if from_csv:
            df = pd.read_csv(source)
        else:
            df = pd.read_csv(source)

        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at')

        # Basic preprocessing
        df['water_liters'] = df['field1'].astype(float)
        df['usage_rate'] = df['water_liters'].diff()

        # Summary stats
        summaries[tank] = {
            "Start Date": str(df['created_at'].min().date()),
            "End Date": str(df['created_at'].max().date()),
            "Total Records": len(df),
            "Total Water Used (L)": round(df['usage_rate'].sum(skipna=True), 2),
            "Average Daily Use (L)": round(df.resample('D', on='created_at')['usage_rate'].sum().mean(), 2)
        }

        # Daily trend
        daily[tank] = df.resample('D', on='created_at')['usage_rate'].sum()

        # Hourly trend
        hourly[tank] = df.resample('H', on='created_at')['usage_rate'].sum()

        # Weekly summary
        week_df = df.resample('W-Mon', on='created_at').agg({
            'water_liters': 'sum',
            'usage_rate': 'sum'
        }).rename(columns={"usage_rate": "water_diff"})
        week_df.index.name = "week"
        weekly[tank] = week_df

        # Anomalies (e.g., high usage spikes)
        anomaly_df = df[df['usage_rate'] > df['usage_rate'].mean() + 2*df['usage_rate'].std()]
        anomalies[tank] = anomaly_df

        # For comparison chart
        comp_df = df[['created_at', 'water_liters']].copy()
        comp_df['Tank'] = tank
        comparison_data.append(comp_df)

    comparison = pd.concat(comparison_data).reset_index(drop=True)

    return {
        "summaries": summaries,
        "daily": daily,
        "hourly": hourly,
        "weekly": weekly,
        "anomalies": anomalies,
        "comparison": comparison
    }

