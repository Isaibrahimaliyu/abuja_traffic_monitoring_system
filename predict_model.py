
import pandas as pd
import joblib
from datetime import datetime
import argparse
import sys
import os

class RealTimeTrafficPredictor:
    def __init__(self, model_prefix='traffic_model'):
        self.models = {}
        self.label_encoders = {}
        self.feature_columns = []
        self.load_models(model_prefix)
    
    def load_models(self, model_prefix):
        """Load trained models with detailed debugging"""
        print("🔍 Loading models...")
        
        # List of required model files
        required_files = [
            f'{model_prefix}_traffic_status.pkl',
            f'{model_prefix}_delay.pkl', 
            f'{model_prefix}_duration.pkl',
            f'{model_prefix}_speed.pkl',
            f'{model_prefix}_encoders.pkl',
            f'{model_prefix}_features.pkl'
        ]
        
        # Check if files exist
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing model files:")
            for file in missing_files:
                print(f"   - {file}")
            print(f"\n💡 Please run 'python train_model.py' first to train the models.")
            return False
        
        try:
            # Load all trained models
            print("📁 Loading model files...")
            self.models['traffic_status'] = joblib.load(f'{model_prefix}_traffic_status.pkl')
            self.models['delay'] = joblib.load(f'{model_prefix}_delay.pkl')
            self.models['duration'] = joblib.load(f'{model_prefix}_duration.pkl')
            self.models['speed'] = joblib.load(f'{model_prefix}_speed.pkl')
            
            # Load encoders and feature list
            self.label_encoders = joblib.load(f'{model_prefix}_encoders.pkl')
            self.feature_columns = joblib.load(f'{model_prefix}_features.pkl')
            
            print("✅ All models loaded successfully!")
            print(f"   - Traffic Status Model: ✓")
            print(f"   - Delay Model: ✓")
            print(f"   - Duration Model: ✓") 
            print(f"   - Speed Model: ✓")
            print(f"   - Feature Encoders: ✓")
            print(f"   - Feature List: {len(self.feature_columns)} features")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict_route(self, route_name, origin, destination, distance_km, target_time=None):"""Predict traffic for a route at specific time"""
    if target_time is None:
        target_time = datetime.now()
    
    print(f"🔮 Making prediction for {route_name} at {target_time.strftime('%H:%M')}...")
    
    # Extract time features
    hour = target_time.hour
    day_of_week_str = target_time.strftime('%A')
    is_weekend = 1 if target_time.weekday() >= 5 else 0
    is_rush_hour = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0
    
    # Convert day of week to numerical
    day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
                  'Friday': 4, 'Saturday': 5, 'Sunday': 6}
    day_of_week_num = day_mapping[day_of_week_str]
    
    # Time of day categories
    if hour < 6:
        time_of_day = 'Late Night'
    elif hour <= 9:
        time_of_day = 'Morning Rush'
    elif hour <= 16:
        time_of_day = 'Day'
    elif hour <= 19:
        time_of_day = 'Evening Rush'
    else:
        time_of_day = 'Night'
    
    # Create features dictionary - use numerical day_of_week
    features = {
        'hour': hour,
        'month': target_time.month,
        'day_of_month': target_time.day,
        'minute': target_time.minute,
        'day_of_week': day_of_week_num,  # Use numerical value instead of string
        'is_weekend': is_weekend,
        'is_rush_hour': is_rush_hour,
        'distance_km': distance_km,
        'route_name': route_name,
        'origin': origin,
        'destination': destination,
        'time_of_day': time_of_day,
        'speed_category': 'Moderate',
        'distance_speed_ratio': distance_km / 40,
        'rush_hour_distance': is_rush_hour * distance_km
    }
    
    print(f"   Features: hour={hour}, rush_hour={is_rush_hour}, distance={distance_km}km, day_of_week={day_of_week_num}")
    
    # Encode categorical features
    X_pred = pd.DataFrame([features])
    
    for col in ['route_name', 'origin', 'destination', 'time_of_day', 'speed_category']:
        if col in self.label_encoders:
            try:
                X_pred[col] = self.label_encoders[col].transform([features[col]])
                print(f"   Encoded {col}: {features[col]} -> {X_pred[col].iloc[0]}")
            except ValueError:
                # If label not seen during training, use default value
                X_pred[col] = 0
                print(f"   ⚠️  Unknown {col}, using default: 0")
    
    # Ensure all feature columns are present
    for col in self.feature_columns:
        if col not in X_pred.columns:
            X_pred[col] = 0
            print(f"   ⚠️  Added missing feature: {col} = 0")
    
    X_pred = X_pred[self.feature_columns]
    print(f"   Final feature vector shape: {X_pred.shape}")
    
    # Make predictions
    try:
        traffic_status = self.models['traffic_status'].predict(X_pred)[0]
        delay_minutes = max(0, round(self.models['delay'].predict(X_pred)[0], 1))
        duration_minutes = max(distance_km, round(self.models['duration'].predict(X_pred)[0], 1))
        speed_kmh = max(5, min(120, round(self.models['speed'].predict(X_pred)[0], 1)))
        
        predictions = {
            'route_name': route_name,
            'origin': origin,
            'destination': destination,
            'traffic_status': traffic_status,
            'delay_minutes': delay_minutes,
            'duration_minutes': duration_minutes,
            'speed_kmh': speed_kmh,
            'timestamp': target_time.strftime('%Y-%m-%d %H:%M:%S'),
            'distance_km': distance_km,
            'time_of_day': time_of_day
        }
        
        print(f"   ✅ Prediction successful!")
        return predictions
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        import traceback
        traceback.print_exc()
        return None

def display_prediction(prediction):
    """Display prediction results in a nice format"""
    if not prediction:
        print("❌ No prediction results to display")
        return
    
    # Color coding for traffic status
    status_colors = {
        'No Traffic': '🟢',
        'Light Traffic': '🟡', 
        'Moderate Traffic': '🟠',
        'Heavy Traffic': '🔴'
    }
    
    color = status_colors.get(prediction['traffic_status'], '⚪')
    
    print(f"\n📍 Route: {prediction['route_name']}")
    print(f"🕒 Time: {prediction['timestamp']} ({prediction['time_of_day']})")
    print(f"📏 Distance: {prediction['distance_km']} km")
    print(f"\n📊 PREDICTION RESULTS:")
    print(f"   {color} Traffic: {prediction['traffic_status']}")
    print(f"   ⏱️  Expected Delay: {prediction['delay_minutes']} minutes")
    print(f"   🕒 Total Duration: {prediction['duration_minutes']} minutes")
    print(f"   🚗 Average Speed: {prediction['speed_kmh']} km/h")
    
    # Additional advice based on prediction
    if prediction['traffic_status'] == 'Heavy Traffic':
        print(f"\n💡 Suggestion: Consider alternative routes or travel later")
        print(f"   🚗 Leave {prediction['delay_minutes']} minutes earlier")
    elif prediction['traffic_status'] == 'Moderate Traffic':
        print(f"\n💡 Suggestion: Moderate traffic expected")
        print(f"   ⏰ Allow extra {prediction['delay_minutes']} minutes for your journey")
    elif prediction['traffic_status'] == 'Light Traffic':
        print(f"\n💡 Suggestion: Good time to travel")
        print(f"   ✅ Smooth journey expected")
    else:
        print(f"\n💡 Suggestion: Clear roads ahead!")
        print(f"   🎉 Perfect driving conditions")

def main():
    """Main function for traffic prediction"""
    
    print("\n🚗 ABUJA TRAFFIC PREDICTION SYSTEM")
    print("="*60)
    
    # Initialize predictor
    predictor = RealTimeTrafficPredictor()
    
    # Check if models loaded successfully
    if not predictor.models:
        print("❌ Cannot proceed without trained models.")
        print("💡 Please run 'python train_model.py' first to train the models.")
        sys.exit(1)
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description='🚗 Abuja Traffic Prediction System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python predict_traffic.py
  python predict_traffic.py --route "Kubwa to CBD" --origin "Kubwa" --destination "CBD" --distance 4.04
  python predict_traffic.py --route "Nyanya to Wuse" --origin "Nyanya" --destination "Wuse" --distance 24.31 --time "08:00" --date "2025-10-30"
        '''
    )
    
    parser.add_argument('--route', type=str, help='Route name (e.g., "Kubwa to CBD")')
    parser.add_argument('--origin', type=str, help='Origin location')
    parser.add_argument('--destination', type=str, help='Destination location')
    parser.add_argument('--distance', type=float, help='Distance in km')
    parser.add_argument('--time', type=str, default=None, help='Time in format HH:MM (24-hour)')
    parser.add_argument('--date', type=str, default=None, help='Date in format YYYY-MM-DD')
    
    args = parser.parse_args()
    
    # Test with predefined routes if no arguments provided
    if not any([args.route, args.origin, args.destination, args.distance]):
        print("No specific route provided. Showing predictions for common routes...\n")
        
        # Common Abuja routes from your data
        common_routes = [
            {"name": "Kubwa to CBD", "origin": "Kubwa", "dest": "Central Business District", "distance": 4.04},
            {"name": "Nyanya to Wuse", "origin": "Nyanya", "dest": "Wuse 2", "distance": 24.31},
            {"name": "Airport to Maitama", "origin": "Airport Road", "dest": "Maitama", "distance": 41.36},
            {"name": "Gwarinpa to CBD", "origin": "Gwarinpa", "dest": "CBD", "distance": 15.93},
            {"name": "Lugbe to Area 1", "origin": "Lugbe", "dest": "Area 1", "distance": 35.45},
        ]
        
        # Test different times
        test_times = [
            ("🌅 Morning Rush (8:00 AM)", datetime.now().replace(hour=8, minute=0, second=0)),
            ("🌞 Afternoon (2:00 PM)", datetime.now().replace(hour=14, minute=0, second=0)),
            ("🌇 Evening Rush (6:00 PM)", datetime.now().replace(hour=18, minute=0, second=0)),
        ]
        
        for time_label, test_time in test_times:
            print(f"\n{time_label}")
            print("-" * 50)
            
            predictions_made = 0
            for route in common_routes:
                prediction = predictor.predict_route(
                    route['name'],
                    route['origin'],
                    route['dest'],
                    route['distance'],
                    test_time
                )
                
                if prediction:
                    color = '🟢' if prediction['traffic_status'] == 'No Traffic' else '🟡' if prediction['traffic_status'] == 'Light Traffic' else '🟠' if prediction['traffic_status'] == 'Moderate Traffic' else '🔴'
                    print(f"{color} {prediction['route_name']:25} | Delay: {prediction['delay_minutes']:4.1f} min | Speed: {prediction['speed_kmh']:5.1f} km/h")
                    predictions_made += 1
                else:
                    print(f"❌ Failed to predict: {route['name']}")
            
            if predictions_made == 0:
                print("❌ No predictions were successful")
    
    else:
        # Use provided arguments
        if not all([args.route, args.origin, args.destination, args.distance]):
            print("❌ Error: Please provide all route information (--route, --origin, --destination, --distance)")
            print("💡 Example: python predict_traffic.py --route 'Kubwa to CBD' --origin 'Kubwa' --destination 'CBD' --distance 4.04")
            return
        
        # Parse custom time
        if args.time and args.date:
            try:
                time_str = f"{args.date} {args.time}"
                target_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                print(f"📅 Using custom time: {target_time}")
            except ValueError:
                print("❌ Error: Invalid date/time format. Use YYYY-MM-DD for date and HH:MM for time")
                print("💡 Example: --date '2025-10-30' --time '08:00'")
                return
        else:
            target_time = datetime.now()
            print(f"🕒 Using current time: {target_time}")
        
        # Make prediction
        prediction = predictor.predict_route(
            args.route,
            args.origin,
            args.destination,
            args.distance,
            target_time
        )
        
        if prediction:
            print(f"\n{'='*60}")
            print("🎯 TRAFFIC PREDICTION RESULTS")
            print(f"{'='*60}")
            display_prediction(prediction)
            print(f"{'='*60}")
        else:
            print("❌ Failed to generate prediction")

def quick_predict():
    """Quick prediction function for common routes"""
    print("\n🚀 QUICK PREDICTIONS")
    print("-" * 40)
    
    predictor = RealTimeTrafficPredictor()
    
    if not predictor.models:
        print("❌ Models not loaded - cannot make quick predictions")
        return
    
    # Quick predictions for right now
    current_time = datetime.now()
    print(f"⏰ Current Time: {current_time.strftime('%H:%M')}")
    print("-" * 40)
    
    quick_routes = [
        {"name": "Kubwa to CBD", "origin": "Kubwa", "dest": "Central Business District", "distance": 4.04},
        {"name": "Nyanya to Wuse", "origin": "Nyanya", "dest": "Wuse 2", "distance": 24.31},
    ]
    
    predictions_made = 0
    for route in quick_routes:
        prediction = predictor.predict_route(
            route['name'],
            route['origin'],
            route['dest'], 
            route['distance'],
            current_time
        )
        
        if prediction:
            color = '🟢' if prediction['traffic_status'] == 'No Traffic' else '🟡' if prediction['traffic_status'] == 'Light Traffic' else '🟠' if prediction['traffic_status'] == 'Moderate Traffic' else '🔴'
            status_icon = color
            print(f"{status_icon} {prediction['route_name']:20} | {prediction['traffic_status']:15} | {prediction['duration_minutes']:4.1f} min")
            predictions_made += 1
    
    if predictions_made == 0:
        print("❌ No quick predictions available")

if __name__ == "__main__":
    main()
    
    # Show quick predictions at the end
    quick_predict()
    
    print(f"\n🎉 Prediction session completed!")