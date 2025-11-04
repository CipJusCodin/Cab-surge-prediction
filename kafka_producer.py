from kafka import KafkaProducer
import pandas as pd
import json
import time

# Load data
df = pd.read_csv(r'C:\Users\yatha\Desktop\BDA project\Datasets\cab_rides.csv')

# Setup Kafka
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

print("Sending rides to Kafka...")

# Send 100 rides
for i, (_, ride) in enumerate(df.sample(100).iterrows(), 1):
    event = {
        'id': i,
        'timestamp': int(ride['time_stamp']),
        'source': ride['source'],
        'destination': ride['destination'],
        'distance': float(ride['distance']),
        'cab_type': ride['cab_type'],
        'actual_surge': float(ride['surge_multiplier'])
    }
    
    producer.send('rides', value=event)
    print(f"[{i}] {event['source']} → {event['destination']}")
    time.sleep(0.5)

print("Done!")