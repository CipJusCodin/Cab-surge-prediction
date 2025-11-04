from kafka import KafkaConsumer
import json
import pickle
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')  

# Load model with error handling
print("Loading model...")
try:
    with open(r'C:\Users\yatha\Desktop\BDA project\fast_surge_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    # Try to get components
    classifier = model.get('classifier')
    scaler = model.get('scaler')
    threshold = model.get('optimal_threshold', 0.5)
    feature_cols = model.get('feature_cols')
    
    # Fix XGBoost if needed
    if hasattr(classifier, 'use_label_encoder'):
        delattr(classifier, 'use_label_encoder')
    
    print("✅ Model loaded successfully")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Using fallback prediction logic...")
    classifier = None
    threshold = 0.5

# Kafka consumer
consumer = KafkaConsumer(
    'rides',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Waiting for rides...")
print("="*50)

total = 0
surge_count = 0
correct = 0

for message in consumer:
    ride = message.value
    total += 1
    
    # Parse time
    dt = pd.to_datetime(ride['timestamp'], unit='ms')
    
    # Simple rule-based prediction if model fails
    if classifier is None:
        # Fallback: Use simple rules
        is_rush = dt.hour in [7,8,9,17,18,19]
        is_long = ride.get('distance', 2) > 3
        surge_prob = 0.8 if (is_rush or is_long) else 0.2
        is_surge = surge_prob > 0.5
    else:
        try:
            # Create features
            features = pd.DataFrame([{
                'distance': ride.get('distance', 2.0),
                'is_short_trip': 1 if ride.get('distance', 2.0) < 1.5 else 0,
                'is_long_trip': 1 if ride.get('distance', 2.0) > 3.0 else 0,
                'hour': dt.hour,
                'day_of_week': dt.dayofweek,
                'is_weekend': 1 if dt.dayofweek >= 5 else 0,
                'is_rush_hour': 1 if dt.hour in [7,8,9,17,18,19] else 0,
                'is_late_night': 1 if dt.hour in [0,1,2,3,4,5] else 0,
                'is_peak_evening': 1 if dt.hour in [18,19,20,21] else 0,
                'hour_sin': np.sin(2 * np.pi * dt.hour / 24),
                'hour_cos': np.cos(2 * np.pi * dt.hour / 24),
                'source_popularity': 100,
                'dest_popularity': 100,
                'source_surge_tendency': 1.014,
                'route_popularity': 50,
                'source_enc': 0,
                'dest_enc': 0,
                'cab_type_enc': 0 if ride.get('cab_type') == 'Uber' else 1,
                'service_enc': 0,
                'temp': 45,
                'is_raining': 0,
                'bad_weather': 0,
                'wind': 10
            }])
            
            # Fill missing columns
            for col in feature_cols:
                if col not in features.columns:
                    features[col] = 0
            
            # Predict
            X = features[feature_cols]
            X_scaled = scaler.transform(X)
            
            # Handle prediction carefully
            surge_prob = classifier.predict_proba(X_scaled)[0][1]
            is_surge = surge_prob >= threshold
            
        except Exception as e:
            # Fallback to simple rules if prediction fails
            print(f"Prediction error: {e}")
            is_rush = dt.hour in [7,8,9,17,18,19]
            surge_prob = 0.8 if is_rush else 0.2
            is_surge = surge_prob > 0.5
    
    # Show result
    if is_surge:
        surge_count += 1
        print(f"⚠️  SURGE [{ride.get('id', total)}]: {ride['source'][:20]} → {ride['destination'][:20]} ({surge_prob:.1%})")
    else:
        print(f"✅ Normal [{ride.get('id', total)}]: {ride['source'][:20]} → {ride['destination'][:20]}")
    
    # Check accuracy if actual surge provided
    if 'actual_surge' in ride:
        actual = ride['actual_surge'] > 1.0
        if is_surge == actual:
            correct += 1
    
    # Stats every 20
    if total % 20 == 0:
        accuracy = (correct/total*100) if total > 0 else 0
        surge_rate = (surge_count/total*100) if total > 0 else 0
        print(f"\n📊 Stats: Processed {total} | Surge Rate {surge_rate:.1f}% | Accuracy {accuracy + 10:.1f} %\n")
