
import streamlit as st
import pandas as pd
import joblib
from datetime import datetime, time
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Abuja Traffic Predictor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TrafficPredictor:
    def __init__(self):
        self.models = {}
        self.label_encoders = {}
        self.feature_columns = []
        self.load_models()
    
    def load_models(self):
        """Load trained models"""
        try:
            # Load models
            self.models['traffic_status'] = joblib.load('traffic_model_traffic_status.pkl')
            self.models['delay'] = joblib.load('traffic_model_delay.pkl')
            self.models['duration'] = joblib.load('traffic_model_duration.pkl')
            self.models['speed'] = joblib.load('traffic_model_speed.pkl')
            
            # Load encoders and features
            self.label_encoders = joblib.load('traffic_model_encoders.pkl')
            self.feature_columns = joblib.load('traffic_model_features.pkl')
            
            return True
        except Exception as e:
            st.error(f"❌ Error loading models: {e}")
            st.info("Please make sure you've run the training script first and all model files are in the same directory.")
            return False
    
    def predict(self, route_name, origin, destination, distance_km, target_time=None):
        """Predict traffic conditions"""
        if target_time is None:
            target_time = datetime.now()
        
        # Prepare features
        hour = target_time.hour
        is_weekend = 1 if target_time.weekday() >= 5 else 0
        is_rush_hour = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0
        day_of_week_num = target_time.weekday()
        
        # Create feature dictionary
        features = {
            'hour': hour,
            'is_weekend': is_weekend,
            'is_rush_hour': is_rush_hour,
            'distance_km': distance_km,
            'day_of_week_num': day_of_week_num,
            'route_name': route_name,
            'origin': origin,
            'destination': destination
        }
        
        # Create DataFrame and encode categorical features
        X_pred = pd.DataFrame([features])
        for col in ['route_name', 'origin', 'destination']:
            if col in self.label_encoders:
                try:
                    X_pred[col] = self.label_encoders[col].transform([features[col]])
                except:
                    X_pred[col] = 0
        
        # Ensure correct column order
        X_pred = X_pred[self.feature_columns]
        
        # Make predictions
        traffic_status = self.models['traffic_status'].predict(X_pred)[0]
        delay = max(0, round(self.models['delay'].predict(X_pred)[0], 1))
        duration = max(distance_km, round(self.models['duration'].predict(X_pred)[0], 1))
        speed = max(5, min(120, round(self.models['speed'].predict(X_pred)[0], 1)))
        
        return {
            'route_name': route_name,
            'traffic_status': traffic_status,
            'delay_minutes': delay,
            'duration_minutes': duration,
            'speed_kmh': speed,
            'timestamp': target_time,
            'distance_km': distance_km,
            'origin': origin,
            'destination': destination
        }

def main():
    # Initialize predictor
    predictor = TrafficPredictor()
    
    # Header
    st.title("🚗 Abuja Traffic Prediction System")
    st.markdown("Predict traffic conditions, delays, and travel times across Abuja")
    
    # Sidebar
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox(
        "Choose Mode",
        ["Quick Predictions", "Custom Route", "Route Comparison", "About"]
    )
    
    # Common routes data
    common_routes = [
        {"name": "Kubwa to CBD", "origin": "Kubwa", "dest": "Central Business District", "distance": 4.04},
        {"name": "Nyanya to Wuse", "origin": "Nyanya", "dest": "Wuse 2", "distance": 24.31},
        {"name": "Airport to Maitama", "origin": "Airport Road", "dest": "Maitama", "distance": 41.36},
        {"name": "Gwarinpa to CBD", "origin": "Gwarinpa", "dest": "CBD", "distance": 15.93},
        {"name": "Lugbe to Area 1", "origin": "Lugbe", "dest": "Area 1", "distance": 35.45},
        {"name": "Kuje to Central", "origin": "Kuje", "dest": "Central Area", "distance": 40.56},
    ]
    
    if app_mode == "Quick Predictions":
        show_quick_predictions(predictor, common_routes)
    
    elif app_mode == "Custom Route":
        show_custom_route(predictor, common_routes)
    
    elif app_mode == "Route Comparison":
        show_route_comparison(predictor, common_routes)
    
    elif app_mode == "About":
        show_about()

def show_quick_predictions(predictor, common_routes):
    st.header("🚀 Quick Predictions")
    
    # Time selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input("Select Date", datetime.now())
    
    with col2:
        selected_time = st.time_input("Select Time", datetime.now().time())
    
    target_datetime = datetime.combine(selected_date, selected_time)
    
    # Display predictions
    st.subheader(f"Predictions for {target_datetime.strftime('%A, %B %d at %H:%M')}")
    
    predictions = []
    for route in common_routes:
        prediction = predictor.predict(
            route['name'], route['origin'], route['dest'], route['distance'], target_datetime
        )
        predictions.append(prediction)
    
    # Create metrics
    cols = st.columns(4)
    
    total_delay = sum(p['delay_minutes'] for p in predictions)
    avg_speed = sum(p['speed_kmh'] for p in predictions) / len(predictions)
    heavy_traffic = sum(1 for p in predictions if p['traffic_status'] == 'Heavy Traffic')
    
    with cols[0]:
        st.metric("Total Routes", len(predictions))
    with cols[1]:
        st.metric("Avg Delay", f"{total_delay/len(predictions):.1f} min")
    with cols[2]:
        st.metric("Avg Speed", f"{avg_speed:.1f} km/h")
    with cols[3]:
        st.metric("Heavy Traffic Routes", heavy_traffic)
    
    # Display predictions in a nice layout
    for i, pred in enumerate(predictions):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.write(f"**{pred['route_name']}**")
                st.caption(f"{pred['origin']} → {pred['destination']}")
            
            with col2:
                status_color = {
                    'No Traffic': 'green',
                    'Light Traffic': 'blue', 
                    'Moderate Traffic': 'orange',
                    'Heavy Traffic': 'red'
                }
                st.markdown(
                    f"<span style='color: {status_color[pred['traffic_status']]}; font-weight: bold;'>{pred['traffic_status']}</span>",
                    unsafe_allow_html=True
                )
            
            with col3:
                st.write(f"⏱️ {pred['delay_minutes']} min delay")
                st.write(f"🕒 {pred['duration_minutes']} min total")
            
            with col4:
                st.write(f"🚗 {pred['speed_kmh']} km/h")
                st.write(f"📏 {pred['distance_km']} km")
            
            st.divider()

def show_custom_route(predictor, common_routes):
    st.header("📍 Custom Route Prediction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Route selection or custom input
        route_option = st.radio(
            "Choose route input method:",
            ["Select from common routes", "Enter custom route"]
        )
        
        if route_option == "Select from common routes":
            selected_route = st.selectbox(
                "Select Route",
                options=[r['name'] for r in common_routes],
                format_func=lambda x: x
            )
            route_data = next(r for r in common_routes if r['name'] == selected_route)
            origin = route_data['origin']
            destination = route_data['dest']
            distance = route_data['distance']
        else:
            origin = st.text_input("Origin", placeholder="e.g., Kubwa")
            destination = st.text_input("Destination", placeholder="e.g., Central Business District")
            distance = st.number_input("Distance (km)", min_value=0.1, max_value=200.0, value=10.0, step=0.1)
            route_name = f"{origin} to {destination}"
    
    with col2:
        # Time selection
        selected_date = st.date_input("Travel Date", datetime.now())
        selected_time = st.time_input("Travel Time", datetime.now().time())
        target_datetime = datetime.combine(selected_date, selected_time)
        
        # Day of week info
        day_info = target_datetime.strftime('%A')
        is_weekend = target_datetime.weekday() >= 5
        st.info(f"📅 {day_info} {'(Weekend)' if is_weekend else '(Weekday)'}")
    
    if st.button("🚀 Predict Traffic", type="primary"):
        if route_option == "Select from common routes":
            route_name = selected_route
        else:
            route_name = f"{origin} to {destination}"
            if not origin or not destination:
                st.error("Please enter both origin and destination")
                return
        
        with st.spinner("Analyzing traffic conditions..."):
            prediction = predictor.predict(route_name, origin, destination, distance, target_datetime)
        
        # Display results
        st.success("Prediction Complete!")
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = {
                'No Traffic': '🟢',
                'Light Traffic': '🟡',
                'Moderate Traffic': '🟠', 
                'Heavy Traffic': '🔴'
            }
            st.metric(
                "Traffic Condition", 
                f"{status_color[prediction['traffic_status']]} {prediction['traffic_status']}"
            )
        
        with col2:
            st.metric("Expected Delay", f"{prediction['delay_minutes']} minutes")
        
        with col3:
            st.metric("Travel Duration", f"{prediction['duration_minutes']} minutes")
        
        with col4:
            st.metric("Average Speed", f"{prediction['speed_kmh']} km/h")
        
        # Detailed information
        st.subheader("📊 Journey Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Route:** {prediction['origin']} → {prediction['destination']}")
            st.info(f"**Distance:** {prediction['distance_km']} km")
            st.info(f"**Scheduled Time:** {prediction['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            # Traffic advice
            advice = {
                'No Traffic': "Perfect driving conditions! No significant delays expected.",
                'Light Traffic': "Good time to travel. Minimal delays expected.",
                'Moderate Traffic': "Moderate traffic. Allow some extra time for your journey.",
                'Heavy Traffic': "Heavy traffic expected. Consider alternative routes or travel times."
            }
            st.warning(f"💡 **Advice:** {advice[prediction['traffic_status']]}")
            
            if prediction['delay_minutes'] > 10:
                st.error(f"🚨 Leave **{prediction['delay_minutes']} minutes earlier** to arrive on time!")

def show_route_comparison(predictor, common_routes):
    st.header("📊 Route Comparison")
    
    st.write("Compare traffic conditions across multiple routes at the same time")
    
    # Time selection
    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.date_input("Comparison Date", datetime.now())
    with col2:
        selected_time = st.time_input("Comparison Time", datetime.now().time())
    
    target_datetime = datetime.combine(selected_date, selected_time)
    
    # Route selection
    selected_routes = st.multiselect(
        "Select routes to compare:",
        options=[r['name'] for r in common_routes],
        default=[r['name'] for r in common_routes[:3]]
    )
    
    if st.button("Compare Routes", type="primary"):
        if not selected_routes:
            st.error("Please select at least one route")
            return
        
        predictions = []
        for route_name in selected_routes:
            route_data = next(r for r in common_routes if r['name'] == route_name)
            prediction = predictor.predict(
                route_name, route_data['origin'], route_data['dest'], 
                route_data['distance'], target_datetime
            )
            predictions.append(prediction)
        
        # Create comparison chart
        df_comparison = pd.DataFrame(predictions)
        
        # Bar chart for delays
        fig_delay = px.bar(
            df_comparison, 
            x='route_name', 
            y='delay_minutes',
            title='Expected Delay by Route',
            color='delay_minutes',
            color_continuous_scale='RdYlGn_r'
        )
        fig_delay.update_layout(xaxis_title="Route", yaxis_title="Delay (minutes)")
        st.plotly_chart(fig_delay, use_container_width=True)
        
        # Bar chart for speeds
        fig_speed = px.bar(
            df_comparison,
            x='route_name',
            y='speed_kmh',
            title='Average Speed by Route',
            color='speed_kmh',
            color_continuous_scale='RdYlGn'
        )
        fig_speed.update_layout(xaxis_title="Route", yaxis_title="Speed (km/h)")
        st.plotly_chart(fig_speed, use_container_width=True)
        
        # Traffic status distribution
        status_counts = df_comparison['traffic_status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Traffic Condition Distribution'
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Detailed table
        st.subheader("Detailed Comparison")
        display_df = df_comparison[['route_name', 'traffic_status', 'delay_minutes', 'duration_minutes', 'speed_kmh', 'distance_km']].copy()
        display_df.columns = ['Route', 'Traffic', 'Delay (min)', 'Duration (min)', 'Speed (km/h)', 'Distance (km)']
        st.dataframe(display_df, use_container_width=True)

def show_about():
    st.header("About Abuja Traffic Predictor")
    
    st.markdown("""
    ### 🚗 How It Works
    
    This traffic prediction system uses machine learning to forecast traffic conditions across Abuja. 
    The model has been trained on historical traffic data and considers:
    
    - **Time factors**: Hour of day, day of week, weekends vs weekdays
    - **Route characteristics**: Distance, origin, destination
    - **Traffic patterns**: Rush hours, typical congestion patterns
    
    ### 📊 Prediction Features
    
    - **Traffic Status**: No Traffic, Light Traffic, Moderate Traffic, or Heavy Traffic
    - **Expected Delay**: Additional time needed due to traffic
    - **Travel Duration**: Total journey time including delays
    - **Average Speed**: Expected speed during the journey
    
    ### 🎯 How to Use
    
    1. **Quick Predictions**: Get instant predictions for common routes
    2. **Custom Route**: Predict traffic for any specific route
    3. **Route Comparison**: Compare multiple routes to choose the best option
    
    ### ℹ️ Note
    
    Predictions are based on typical traffic patterns and may vary due to:
    - Special events
    - Road construction
    - Weather conditions
    - Accidents or incidents
    """)
    
    st.info("""
    💡 **Tip**: For the most accurate predictions, use this tool during typical commuting hours 
    when traffic patterns are most predictable.
    """)

if __name__ == "__main__":
    main()