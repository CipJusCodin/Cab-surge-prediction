import pandas as pd
import numpy as np

print("="*60)
print("HADOOP/SPARK SURGE ANALYSIS (Simulation)")
print("="*60)

# Load data
df = pd.read_csv(r'C:\Users\yatha\Desktop\BDA project\Datasets\cab_rides.csv')
print(f"\nTotal rides in HDFS: {len(df):,}")

# Convert timestamp
df['hour'] = pd.to_datetime(df['time_stamp'], unit='ms').dt.hour

# Job 1: Surge distribution
print("\n[MapReduce Job 1] Surge Distribution:")
surge_counts = df['surge_multiplier'].value_counts().sort_index()
for mult, count in surge_counts.items():
    print(f"  {mult:.2f}x: {count:,} ({count/len(df)*100:.1f}%)")

# Job 2: Hourly patterns
print("\n[MapReduce Job 2] Hourly Surge Patterns:")
hourly = df.groupby('hour')['surge_multiplier'].agg(['mean', 'count'])
print("\nHour | Avg Surge | Count")
print("-"*30)
for hour in [7,8,9,12,17,18,19,22]:  # Key hours only
    if hour in hourly.index:
        print(f" {hour:2d}  | {hourly.loc[hour, 'mean']:.4f}  | {hourly.loc[hour, 'count']:,}")

# Job 3: Top surge locations
print("\n[MapReduce Job 3] Top 5 Surge Locations:")
location_surge = df.groupby('source')['surge_multiplier'].mean().nlargest(5)
for loc, surge in location_surge.items():
    print(f"  {loc}: {surge:.4f}x")

print("\n" + "="*60)
print("Analysis complete - Data ready for ML pipeline")
print("="*60)