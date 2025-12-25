
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TrafficPredictor:
    def __init__(self):
        self.models = {}
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def load_and_prepare_data(self, filename='abuja_traffic_data.csv'):
        """Load and prepare the traffic data for training"""
        print("Loading data...")
        df = pd.read_csv(filename)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"Dataset shape: {df.shape}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    
    def create_features(self, df):
        """Create additional features for the model"""
        print("Creating features...")
        
        # Extract time-based features
        df['month'] = df['timestamp'].dt.month
        df['day_of_month'] = df['timestamp'].dt.day
        df['minute'] = df['timestamp'].dt.minute
        
        # FIXED: Create time of day categories without duplicate labels
        df['time_of_day'] = pd.cut(df['hour'], 
                                 bins=[0, 6, 9, 16, 19, 24],
                                 labels=['Late Night', 'Morning Rush', 'Day', 'Evening Rush', 'Night'],
                                 include_lowest=True)
        
        # Route characteristics - FIXED: No duplicate labels
        df['speed_category'] = pd.cut(df['avg_speed_kmh'],
                                   bins=[0, 20, 40, 60, 200],
                                   labels=['Very Slow', 'Slow', 'Moderate', 'Fast'])
        
        # Create interaction features
        df['distance_speed_ratio'] = df['distance_km'] / (df['avg_speed_kmh'] + 1)
        df['rush_hour_distance'] = df['is_rush_hour'] * df['distance_km']
        
        return df
    
    def prepare_training_data(self, df):
        """Prepare data for model training"""
        print("Preparing training data...")
        
        # Features for prediction
        feature_columns = [
            'hour', 'month', 'day_of_month', 'minute', 
            'is_weekend', 'is_rush_hour', 'distance_km', 
            'route_name', 'origin', 'destination',
            'time_of_day', 'speed_category', 'distance_speed_ratio',
            'rush_hour_distance'
        ]
        
        # Encode categorical variables
        categorical_columns = ['route_name', 'origin', 'destination', 'time_of_day', 'speed_category']
        
        X = df[feature_columns].copy()
        
        for col in categorical_columns:
            if col in X.columns:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
        
        # Add day of week as numerical (already encoded in original data)
        if 'day_of_week' in df.columns:
            # Convert day of week to numerical
            day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
                          'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            X['day_of_week'] = df['day_of_week'].map(day_mapping)
            feature_columns.append('day_of_week')
        
        self.feature_columns = feature_columns
        
        # Target variables
        y_traffic_status = df['traffic_status']  # Classification
        y_delay = df['delay_minutes']  # Regression
        y_duration = df['duration_in_traffic_minutes']  # Regression
        y_speed = df['avg_speed_kmh']  # Regression
        
        print(f"Features: {len(feature_columns)}")
        print(f"Target samples: {len(y_traffic_status)}")
        
        return X, y_traffic_status, y_delay, y_duration, y_speed
    
    def train_models(self, X, y_traffic_status, y_delay, y_duration, y_speed):
        """Train multiple models for different predictions"""
        print("Training models...")
        
        # Split data
        X_train, X_test, y_status_train, y_status_test = train_test_split(
            X, y_traffic_status, test_size=0.2, random_state=42, stratify=y_traffic_status
        )
        
        # Train Traffic Status Classifier
        print("Training Traffic Status Classifier...")
        self.models['traffic_status'] = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.models['traffic_status'].fit(X_train, y_status_train)
        
        # For regression targets, use the same split
        X_train_reg, X_test_reg, y_delay_train, y_delay_test = train_test_split(
            X, y_delay, test_size=0.2, random_state=42
        )
        
        y_duration_train = y_duration.iloc[X_train_reg.index]
        y_speed_train = y_speed.iloc[X_train_reg.index]
        
        # Train Delay Predictor
        print("Training Delay Predictor...")
        self.models['delay'] = RandomForestRegressor(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.models['delay'].fit(X_train_reg, y_delay_train)
        
        # Train Duration Predictor
        print("Training Duration Predictor...")
        self.models['duration'] = RandomForestRegressor(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.models['duration'].fit(X_train_reg, y_duration_train)
        
        # Train Speed Predictor
        print("Training Speed Predictor...")
        self.models['speed'] = RandomForestRegressor(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        self.models['speed'].fit(X_train_reg, y_speed_train)
        
        return X_test, y_status_test, X_test_reg, y_delay_test, y_duration.iloc[X_test_reg.index], y_speed.iloc[X_test_reg.index]
    
    def evaluate_models(self, X_test, y_status_test, X_test_reg, y_delay_test, y_duration_test, y_speed_test):
        """Evaluate model performance"""
        print("\n" + "="*60)
        print("MODEL EVALUATION RESULTS")
        print("="*60)
        
        # Evaluate Traffic Status Classifier
        y_status_pred = self.models['traffic_status'].predict(X_test)
        print("\n🚦 TRAFFIC STATUS CLASSIFIER PERFORMANCE:")
        print(classification_report(y_status_test, y_status_pred))
        
        # Confusion Matrix
        plt.figure(figsize=(10, 6))
        cm = confusion_matrix(y_status_test, y_status_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=sorted(y_status_test.unique()),
                   yticklabels=sorted(y_status_test.unique()))
        plt.title('Traffic Status Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Evaluate Regression Models
        print("\n📊 REGRESSION MODELS PERFORMANCE:")
        
        regression_results = []
        
        for target_name in ['delay', 'duration', 'speed']:
            if target_name == 'delay':
                y_true = y_delay_test
                units = 'minutes'
            elif target_name == 'duration':
                y_true = y_duration_test
                units = 'minutes'
            else:
                y_true = y_speed_test
                units = 'km/h'
                
            y_pred = self.models[target_name].predict(X_test_reg)
            
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            
            regression_results.append({
                'model': target_name,
                'mae': mae,
                'r2': r2,
                'units': units
            })
            
            print(f"\n🎯 {target_name.upper()} PREDICTOR:")
            print(f"   Mean Absolute Error: {mae:.2f} {units}")
            print(f"   R² Score: {r2:.2f}")
            
            # Plot predictions vs actual
            plt.figure(figsize=(10, 6))
            plt.scatter(y_true, y_pred, alpha=0.5)
            plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
            plt.xlabel(f'Actual {target_name} ({units})')
            plt.ylabel(f'Predicted {target_name} ({units})')
            plt.title(f'{target_name.title()} Prediction vs Actual\nMAE: {mae:.2f}, R²: {r2:.2f}')
            plt.tight_layout()
            plt.savefig(f'{target_name}_predictions.png', dpi=300, bbox_inches='tight')
            plt.show()
        
        return regression_results
    
    def feature_importance(self, X):
        """Display feature importance"""
        print("\n" + "="*50)
        print("FEATURE IMPORTANCE ANALYSIS")
        print("="*50)
        
        importance = self.models['traffic_status'].feature_importances_
        indices = np.argsort(importance)[::-1]
        
        plt.figure(figsize=(12, 8))
        plt.barh(range(len(indices)), importance[indices])
        plt.yticks(range(len(indices)), [self.feature_columns[i] for i in indices])
        plt.xlabel('Feature Importance')
        plt.title('Traffic Status Prediction - Feature Importance')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print feature importance scores
        print("\nTop 10 Most Important Features:")
        for i in range(min(10, len(indices))):
            print(f"{i+1:2d}. {self.feature_columns[indices[i]]:25} {importance[indices[i]]:.4f}")
    
    def save_models(self, filename_prefix='traffic_model'):
        """Save trained models and encoders"""
        print("\n💾 Saving models...")
        
        # Save models
        for model_name, model in self.models.items():
            joblib.dump(model, f'{filename_prefix}_{model_name}.pkl')
            print(f"   ✓ Saved {model_name} model")
        
        # Save encoders
        joblib.dump(self.label_encoders, f'{filename_prefix}_encoders.pkl')
        joblib.dump(self.feature_columns, f'{filename_prefix}_features.pkl')
        
        print(f"\n✅ All models saved successfully with prefix '{filename_prefix}'!")
        print("   Files created:")
        print("   - traffic_model_traffic_status.pkl")
        print("   - traffic_model_delay.pkl")
        print("   - traffic_model_duration.pkl")
        print("   - traffic_model_speed.pkl")
        print("   - traffic_model_encoders.pkl")
        print("   - traffic_model_features.pkl")
    
    def dataset_statistics(self, df):
        """Display dataset statistics"""
        print("\n" + "="*50)
        print("DATASET STATISTICS")
        print("="*50)
        print(f"📊 Total records: {len(df):,}")
        print(f"📍 Unique routes: {df['route_name'].nunique()}")
        print(f"📅 Date range: {df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}")
        
        print(f"\n🚦 Traffic Status Distribution:")
        status_counts = df['traffic_status'].value_counts()
        for status, count in status_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {status:15}: {count:4d} records ({percentage:.1f}%)")
        
        print(f"\n⏰ Average Delay by Hour:")
        delay_by_hour = df.groupby('hour')['delay_minutes'].mean().round(2)
        for hour, delay in delay_by_hour.items():
            print(f"   {hour:2d}:00 - {delay:5.2f} min delay")
        
        print(f"\n🚗 Speed Statistics:")
        print(f"   Average Speed: {df['avg_speed_kmh'].mean():.1f} km/h")
        print(f"   Max Speed: {df['avg_speed_kmh'].max():.1f} km/h")
        print(f"   Min Speed: {df['avg_speed_kmh'].min():.1f} km/h")

def main():
    """Main function to train and evaluate the model"""
    
    print("🚗 ABUJA TRAFFIC PREDICTION MODEL TRAINING")
    print("="*60)
    
    # Initialize predictor
    predictor = TrafficPredictor()
    
    try:
        # Load data
        df = predictor.load_and_prepare_data('abuja_traffic_data.csv')
        
        # Show dataset statistics
        predictor.dataset_statistics(df)
        
        # Create features
        df = predictor.create_features(df)
        
        # Prepare training data
        X, y_status, y_delay, y_duration, y_speed = predictor.prepare_training_data(df)
        
        # Train models
        print("\n" + "="*50)
        print("STARTING MODEL TRAINING")
        print("="*50)
        
        X_test, y_status_test, X_test_reg, y_delay_test, y_duration_test, y_speed_test = predictor.train_models(
            X, y_status, y_delay, y_duration, y_speed
        )
        
        # Evaluate models
        regression_results = predictor.evaluate_models(
            X_test, y_status_test, X_test_reg, y_delay_test, y_duration_test, y_speed_test
        )
        
        # Show feature importance
        predictor.feature_importance(X)
        
        # Save models
        predictor.save_models()
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now use the trained models for predictions:")
        print("1. Run: python predict_traffic.py")
        print("2. Or specify a route: python predict_traffic.py --route 'Kubwa to CBD' --origin 'Kubwa' --destination 'Central Business District' --distance 4.04")
        
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease make sure:")
        print("1. abuja_traffic_data.csv exists in the same folder")
        print("2. The CSV file has the correct format")
        print("3. You have all required packages installed")

if __name__ == "__main__":
    main()