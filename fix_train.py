
# fix_training.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from datetime import datetime

print("🚗 FIXING MODEL TRAINING AND SAVING...")

# Load the data
df = pd.read_csv('abuja_traffic_data.csv')
print(f"✓ Loaded data: {len(df)} records")

# Create basic features
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['month'] = df['timestamp'].dt.month
df['day_of_month'] = df['timestamp'].dt.day
df['minute'] = df['timestamp'].dt.minute

# Simple feature engineering
df['distance_speed_ratio'] = df['distance_km'] / (df['avg_speed_kmh'] + 1)
df['rush_hour_distance'] = df['is_rush_hour'] * df['distance_km']

# Prepare features
feature_columns = [
    'hour', 'month', 'day_of_month', 'minute', 
    'is_weekend', 'is_rush_hour', 'distance_km', 
    'route_name', 'origin', 'destination',
    'distance_speed_ratio', 'rush_hour_distance'
]

# Encode categorical variables
label_encoders = {}
X = df[feature_columns].copy()

for col in ['route_name', 'origin', 'destination']:
    label_encoders[col] = LabelEncoder()
    X[col] = label_encoders[col].fit_transform(X[col].astype(str))

# Add day of week
day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
              'Friday': 4, 'Saturday': 5, 'Sunday': 6}
X['day_of_week'] = df['day_of_week'].map(day_mapping)
feature_columns.append('day_of_week')

# Target variables
y_traffic_status = df['traffic_status']
y_delay = df['delay_minutes']
y_duration = df['duration_in_traffic_minutes']
y_speed = df['avg_speed_kmh']

print(f"✓ Prepared features: {X.shape}")

# Train models
print("Training models...")

# Traffic Status
status_model = RandomForestClassifier(n_estimators=50, random_state=42)
status_model.fit(X, y_traffic_status)
print("✓ Traffic status model trained")

# Delay
delay_model = RandomForestRegressor(n_estimators=50, random_state=42)
delay_model.fit(X, y_delay)
print("✓ Delay model trained")

# Duration
duration_model = RandomForestRegressor(n_estimators=50, random_state=42)
duration_model.fit(X, y_duration)
print("✓ Duration model trained")

# Speed
speed_model = RandomForestRegressor(n_estimators=50, random_state=42)
speed_model.fit(X, y_speed)
print("✓ Speed model trained")

# Save models
print("\n💾 Saving models...")

try:
    joblib.dump(status_model, 'traffic_model_traffic_status.pkl')
    print("✓ Saved traffic_model_traffic_status.pkl")
    
    joblib.dump(delay_model, 'traffic_model_delay.pkl')
    print("✓ Saved traffic_model_delay.pkl")
    
    joblib.dump(duration_model, 'traffic_model_duration.pkl')
    print("✓ Saved traffic_model_duration.pkl")
    
    joblib.dump(speed_model, 'traffic_model_speed.pkl')
    print("✓ Saved traffic_model_speed.pkl")
    
    joblib.dump(label_encoders, 'traffic_model_encoders.pkl')
    print("✓ Saved traffic_model_encoders.pkl")
    
    joblib.dump(feature_columns, 'traffic_model_features.pkl')
    print("✓ Saved traffic_model_features.pkl")
    
    print("\n🎉 ALL MODELS SAVED SUCCESSFULLY!")
    
except Exception as e:
    print(f"❌ Error saving models: {e}")

# Verify files were created
print("\n🔍 Verifying model files...")
pkl_files = [f for f in os.listdir('.') if f.endswith('.pkl')]
for f in sorted(pkl_files):
    size = os.path.getsize(f)
    print(f"  {f}: {size} bytes")

print(f"\nTotal model files: {len(pkl_files)}/6")