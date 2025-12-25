
import requests
import pandas as pd
from datetime import datetime
import time
import os
import schedule
import random
import concurrent.futures
from threading import Lock
import math

# Configuration
COLLECTION_INTERVAL_MINUTES = 0  # How often to collect data
CSV_FILENAME = 'abuja_traffic_data.csv'
MAX_WORKERS = 5  # Number of parallel threads for route collection
BATCH_SIZE = 20  # Process routes in batches to manage memory and API load

# OSRM API endpoint (free, no API key needed)
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving/"

# Define comprehensive Abuja routes with coordinates (lat, lon)
# Format: (origin_coords, destination_coords, route_name, origin_name, destination_name)
ABUJA_ROUTES = [
    # (lon, lat) format for OSRM
    
    # MAJOR EXPRESS ROUTES
    ([7.4898, 9.0765], [7.4951, 9.0579], "Kubwa to CBD", "Kubwa", "Central Business District"),
    ([7.6544, 9.0390], [7.4951, 9.0579], "Nyanya to Wuse", "Nyanya", "Wuse 2"),
    ([7.2630, 9.0068], [7.4902, 9.0820], "Airport to Maitama", "Airport Road", "Maitama"),
    ([7.3749, 8.8645], [7.4892, 9.0486], "Lugbe to Area 1", "Lugbe", "Area 1"),
    ([7.2252, 8.8818], [7.4892, 9.0486], "Kuje to Central", "Kuje", "Central Area"),
    ([7.0844, 8.9422], [7.4892, 9.0486], "Gwagwalada to City Gate", "Gwagwalada", "City Gate"),
    
    # INNER CITY ROUTES - WUSE/MAITAMA/ASOKORO AREA
    ([7.4690, 9.0614], [7.4951, 9.0579], "Wuse to CBD", "Wuse Market", "Central Business District"),
    ([7.4902, 9.0820], [7.4690, 9.0614], "Maitama to Wuse", "Maitama", "Wuse"),
    ([7.5266, 9.0450], [7.4690, 9.0614], "Asokoro to Wuse", "Asokoro", "Wuse"),
    ([7.5266, 9.0450], [7.4902, 9.0820], "Asokoro to Maitama", "Asokoro", "Maitama"),
    ([7.4951, 9.0579], [7.4902, 9.0820], "CBD to Maitama", "CBD", "Maitama"),
    
    # GARKI/AREA ROUTES
    ([7.4860, 9.0333], [7.4951, 9.0579], "Garki to CBD", "Garki", "CBD"),
    ([7.4892, 9.0486], [7.4860, 9.0333], "Area 1 to Garki", "Area 1", "Garki"),
    ([7.4950, 9.0450], [7.4860, 9.0333], "Area 2 to Garki", "Area 2", "Garki"),
    ([7.5010, 9.0420], [7.4951, 9.0579], "Area 3 to CBD", "Area 3", "CBD"),
    ([7.4860, 9.0333], [7.4690, 9.0614], "Garki to Wuse", "Garki", "Wuse"),
    
    # GWARINPA/DUTSE/KUBWA ROUTES
    ([7.4155, 9.1130], [7.4951, 9.0579], "Gwarinpa to CBD", "Gwarinpa", "CBD"),
    ([7.4336, 9.0765], [7.4155, 9.1130], "Dutse to Gwarinpa", "Dutse", "Gwarinpa"),
    ([7.4898, 9.0765], [7.4155, 9.1130], "Kubwa to Gwarinpa", "Kubwa", "Gwarinpa"),
    ([7.4336, 9.0765], [7.4951, 9.0579], "Dutse to CBD", "Dutse", "CBD"),
    ([7.4336, 9.0765], [7.4690, 9.0614], "Dutse to Wuse", "Dutse", "Wuse"),
    ([7.4155, 9.1130], [7.4690, 9.0614], "Gwarinpa to Wuse", "Gwarinpa", "Wuse"),
    
    # JABI/UTAKO/WUYE ROUTES
    ([7.4569, 9.0530], [7.4951, 9.0579], "Jabi to CBD", "Jabi", "CBD"),
    ([7.4422, 9.0704], [7.4569, 9.0530], "Utako to Jabi", "Utako", "Jabi"),
    ([7.4422, 9.0704], [7.4951, 9.0579], "Utako to CBD", "Utako", "CBD"),
    ([7.4490, 9.0850], [7.4569, 9.0530], "Wuye to Jabi", "Wuye", "Jabi"),
    ([7.4422, 9.0704], [7.4690, 9.0614], "Utako to Wuse", "Utako", "Wuse"),
    ([7.4569, 9.0530], [7.4690, 9.0614], "Jabi to Wuse", "Jabi", "Wuse"),
    
    # KARU/NYANYA/MARABA ROUTES
    ([7.6544, 9.0390], [7.6830, 8.9950], "Nyanya to Karu", "Nyanya", "Karu"),
    ([7.6830, 8.9950], [7.4951, 9.0579], "Karu to CBD", "Karu", "CBD"),
    ([7.6830, 8.9950], [7.4860, 9.0333], "Karu to Garki", "Karu", "Garki"),
    ([7.6544, 9.0390], [7.4860, 9.0333], "Nyanya to Garki", "Nyanya", "Garki"),
    ([7.7345, 8.9513], [7.6544, 9.0390], "Maraba to Nyanya", "Maraba", "Nyanya"),
    
    # LUGBE/AIRPORT ROAD ROUTES
    ([7.3749, 8.8645], [7.2630, 9.0068], "Lugbe to Airport", "Lugbe", "Airport Road"),
    ([7.2630, 9.0068], [7.4951, 9.0579], "Airport to CBD", "Airport Road", "CBD"),
    ([7.3749, 8.8645], [7.4951, 9.0579], "Lugbe to CBD", "Lugbe", "CBD"),
    ([7.3749, 8.8645], [7.4860, 9.0333], "Lugbe to Garki", "Lugbe", "Garki"),
    
    # KUJE/GWAGWALADA ROUTES
    ([7.2252, 8.8818], [7.0844, 8.9422], "Kuje to Gwagwalada", "Kuje", "Gwagwalada"),
    ([7.0844, 8.9422], [7.4951, 9.0579], "Gwagwalada to CBD", "Gwagwalada", "CBD"),
    ([7.2252, 8.8818], [7.3749, 8.8645], "Kuje to Lugbe", "Kuje", "Lugbe"),
    
    # LOKOGOMA/APO/GUDU ROUTES
    ([7.4620, 8.9920], [7.4860, 9.0333], "Lokogoma to Garki", "Lokogoma", "Garki"),
    ([7.4520, 8.9850], [7.4620, 8.9920], "Apo to Lokogoma", "Apo", "Lokogoma"),
    ([7.4350, 9.0100], [7.4860, 9.0333], "Gudu to Garki", "Gudu", "Garki"),
    ([7.4620, 8.9920], [7.4951, 9.0579], "Lokogoma to CBD", "Lokogoma", "CBD"),
    ([7.4520, 9.0150], [7.4860, 9.0333], "Galadimawa to Garki", "Galadimawa", "Garki"),
    
    # MARARABA/MASAKA/KARSHI ROUTES
    ([7.7345, 8.9513], [7.4951, 9.0579], "Maraba to CBD", "Maraba", "CBD"),
    ([7.6234, 8.7512], [7.2252, 8.8818], "Karshi to Kuje", "Karshi", "Kuje"),
    ([7.5820, 8.8330], [7.3749, 8.8645], "Masaka to Lugbe", "Masaka", "Lugbe"),
    
    # LIFE CAMP/JIKWOYI/KURUDU ROUTES
    ([7.4225, 9.0925], [7.4422, 9.0704], "Life Camp to Utako", "Life Camp", "Utako"),
    ([7.5510, 9.0140], [7.4860, 9.0333], "Jikwoyi to Garki", "Jikwoyi", "Garki"),
    ([7.5890, 8.9820], [7.6544, 9.0390], "Kurudu to Nyanya", "Kurudu", "Nyanya"),
    
    # MPAPE/BWARI ROUTES
    ([7.4110, 9.1350], [7.4155, 9.1130], "Mpape to Gwarinpa", "Mpape", "Gwarinpa"),
    ([7.3850, 9.1850], [7.4110, 9.1350], "Bwari to Mpape", "Bwari", "Mpape"),
    ([7.3850, 9.1850], [7.4951, 9.0579], "Bwari to CBD", "Bwari", "CBD"),
    
    # KATAMPE/JAHI ROUTES
    ([7.4380, 9.0950], [7.4902, 9.0820], "Katampe to Maitama", "Katampe", "Maitama"),
    ([7.4520, 9.0880], [7.4690, 9.0614], "Jahi to Wuse", "Jahi", "Wuse"),
    ([7.4380, 9.0950], [7.4569, 9.0530], "Katampe to Jabi", "Katampe", "Jabi"),
    
    # BERGER/KADO/JIKWOYI ROUTES
    ([7.4473, 9.0375], [7.4860, 9.0333], "Berger to Garki", "Berger", "Garki"),
    ([7.4640, 9.0280], [7.4473, 9.0375], "Kado to Berger", "Kado", "Berger"),
    
    # CROSS-CITY COMMUTER ROUTES
    ([7.4898, 9.0765], [7.6544, 9.0390], "Kubwa to Nyanya", "Kubwa", "Nyanya"),
    ([7.4155, 9.1130], [7.3749, 8.8645], "Gwarinpa to Lugbe", "Gwarinpa", "Lugbe"),
    ([7.4902, 9.0820], [7.4860, 9.0333], "Maitama to Garki", "Maitama", "Garki"),
    ([7.4569, 9.0530], [7.5266, 9.0450], "Jabi to Asokoro", "Jabi", "Asokoro"),
    
    # ADDITIONAL ROUTES FOR MORE COMPREHENSIVE COVERAGE
    # WUSE ZONE ROUTES
    ([7.4690, 9.0614], [7.4569, 9.0530], "Wuse to Jabi", "Wuse", "Jabi"),
    ([7.4690, 9.0614], [7.4422, 9.0704], "Wuse to Utako", "Wuse", "Utako"),
    ([7.4690, 9.0614], [7.4860, 9.0333], "Wuse to Garki", "Wuse", "Garki"),
    
    # MAITAMA EXTENSION ROUTES
    ([7.4902, 9.0820], [7.5266, 9.0450], "Maitama to Asokoro", "Maitama", "Asokoro"),
    ([7.4902, 9.0820], [7.4569, 9.0530], "Maitama to Jabi", "Maitama", "Jabi"),
    
    # ASOKORO CONNECTIONS
    ([7.5266, 9.0450], [7.4951, 9.0579], "Asokoro to CBD", "Asokoro", "CBD"),
    ([7.5266, 9.0450], [7.4860, 9.0333], "Asokoro to Garki", "Asokoro", "Garki"),
    
    # GWARINPA EXTENSIONS
    ([7.4155, 9.1130], [7.4336, 9.0765], "Gwarinpa to Dutse", "Gwarinpa", "Dutse"),
    ([7.4155, 9.1130], [7.4898, 9.0765], "Gwarinpa to Kubwa", "Gwarinpa", "Kubwa"),
    
    # KUBWA NETWORK
    ([7.4898, 9.0765], [7.4336, 9.0765], "Kubwa to Dutse", "Kubwa", "Dutse"),
    ([7.4898, 9.0765], [7.4690, 9.0614], "Kubwa to Wuse", "Kubwa", "Wuse"),
    
    # NYANYA/KARU EXPANSION
    ([7.6544, 9.0390], [7.7345, 8.9513], "Nyanya to Maraba", "Nyanya", "Maraba"),
    ([7.6830, 8.9950], [7.7345, 8.9513], "Karu to Maraba", "Karu", "Maraba"),
    
    # LUGBE CORRIDOR
    ([7.3749, 8.8645], [7.4620, 8.9920], "Lugbe to Lokogoma", "Lugbe", "Lokogoma"),
    ([7.3749, 8.8645], [7.4520, 8.9850], "Lugbe to Apo", "Lugbe", "Apo"),
    
    # KUJE AREA EXPANSION
    ([7.2252, 8.8818], [7.0844, 8.9422], "Kuje to Gwagwalada", "Kuje", "Gwagwalada"),
    ([7.2252, 8.8818], [7.3749, 8.8645], "Kuje to Lugbe", "Kuje", "Lugbe"),
    
    # PERIPHERAL CONNECTIONS
    ([7.4110, 9.1350], [7.3850, 9.1850], "Mpape to Bwari", "Mpape", "Bwari"),
    ([7.4225, 9.0925], [7.4155, 9.1130], "Life Camp to Gwarinpa", "Life Camp", "Gwarinpa"),
    
    # SHORT INNER-CITY ROUTES
    ([7.4860, 9.0333], [7.4892, 9.0486], "Garki to Area 1", "Garki", "Area 1"),
    ([7.4892, 9.0486], [7.4950, 9.0450], "Area 1 to Area 2", "Area 1", "Area 2"),
    ([7.4950, 9.0450], [7.5010, 9.0420], "Area 2 to Area 3", "Area 2", "Area 3"),
    ([7.4422, 9.0704], [7.4490, 9.0850], "Utako to Wuye", "Utako", "Wuye"),
]
@app.route("/report")
def report():
    stats = generate_statistics()

    if not stats:
        return "No data available yet."

    return render_template(
        "report.html",
        stats=stats
    )

# Thread-safe lock for file operations
file_lock = Lock()
def generate_statistics():
    if not os.path.exists(CSV_FILENAME):
        return None

    df = pd.read_csv(CSV_FILENAME)

    stats = {
        "total_records": len(df),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "unique_routes": df['route_name'].nunique(),
        "traffic_distribution": df['traffic_status'].value_counts().to_dict(),
        "avg_delay_by_hour": df.groupby('hour')['delay_minutes'].mean().round(2).to_dict()
    }

    return stats

def get_route_info(origin_coords, destination_coords):
    """Get route information from OSRM"""
    
    # Format: lon,lat;lon,lat
    coords_str = f"{origin_coords[0]},{origin_coords[1]};{destination_coords[0]},{destination_coords[1]}"
    url = f"{OSRM_BASE_URL}{coords_str}?overview=false"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['code'] == 'Ok' and len(data['routes']) > 0:
                route = data['routes'][0]
                
                distance_meters = route['distance']
                duration_seconds = route['duration']
                
                return {
                    'distance_meters': distance_meters,
                    'duration_seconds': duration_seconds
                }
        
        return None
        
    except Exception as e:
        print(f"Error fetching route: {str(e)}")
        return None

def process_route_batch(route_batch, current_time):
    """Process a batch of routes in parallel"""
    data_records = []
    
    def process_single_route(route_data):
        origin_coords, dest_coords, route_name, origin_name, dest_name = route_data
        
        try:
            # Get route information from OSRM
            route_info = get_route_info(origin_coords, dest_coords)
            
            if route_info:
                distance_meters = route_info['distance_meters']
                distance_km = distance_meters / 1000
                
                base_duration_seconds = route_info['duration_seconds']
                base_duration_minutes = base_duration_seconds / 60
                
                # Simulate traffic conditions
                day_of_week = current_time.strftime('%A')
                duration_in_traffic_minutes, traffic_multiplier = simulate_traffic_conditions(
                    current_time.hour, 
                    day_of_week, 
                    base_duration_minutes
                )
                
                # Calculate delay
                delay_minutes = duration_in_traffic_minutes - base_duration_minutes
                
                # Determine traffic status
                if delay_minutes < 5:
                    traffic_status = "No Traffic"
                elif delay_minutes < 15:
                    traffic_status = "Light Traffic"
                elif delay_minutes < 30:
                    traffic_status = "Moderate Traffic"
                else:
                    traffic_status = "Heavy Traffic"
                
                # Calculate average speed
                avg_speed_kmh = (distance_km / duration_in_traffic_minutes) * 60 if duration_in_traffic_minutes > 0 else 0
                
                # Record data
                record = {
                    'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': current_time.strftime('%Y-%m-%d'),
                    'time': current_time.strftime('%H:%M:%S'),
                    'day_of_week': day_of_week,
                    'hour': current_time.hour,
                    'is_weekend': 1 if current_time.weekday() >= 5 else 0,
                    'is_rush_hour': 1 if (7 <= current_time.hour <= 9) or (17 <= current_time.hour <= 19) else 0,
                    'route_name': route_name,
                    'origin': origin_name,
                    'destination': dest_name,
                    'distance_km': round(distance_km, 2),
                    'duration_minutes': round(base_duration_minutes, 2),
                    'duration_in_traffic_minutes': round(duration_in_traffic_minutes, 2),
                    'delay_minutes': round(delay_minutes, 2),
                    'avg_speed_kmh': round(avg_speed_kmh, 2),
                    'traffic_status': traffic_status,
                    'traffic_multiplier': round(traffic_multiplier, 2)
                }
                
                print(f"✓ {route_name}: {traffic_status} (Delay: {delay_minutes:.1f} min)")
                return record
            else:
                print(f"✗ No route found for {route_name}")
                return None
                
        except Exception as e:
            print(f"✗ Error collecting data for {route_name}: {str(e)}")
            return None
    
    # Process routes in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_single_route, route) for route in route_batch]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                data_records.append(result)
    
    return data_records

def simulate_traffic_conditions(hour, day_of_week, base_duration_minutes):
    """
    Simulate realistic traffic conditions based on time and day
    Since OpenStreetMap doesn't provide real-time traffic, we simulate it
    based on typical Abuja traffic patterns
    """
    
    traffic_multiplier = 1.0
    
    # Rush hour traffic (7-9 AM and 5-7 PM on weekdays)
    is_weekday = day_of_week not in ['Saturday', 'Sunday']
    
    if is_weekday:
        if 7 <= hour <= 9:
            # Morning rush hour
            traffic_multiplier = random.uniform(1.3, 1.8)
        elif 17 <= hour <= 19:
            # Evening rush hour
            traffic_multiplier = random.uniform(1.5, 2.0)
        elif 12 <= hour <= 14:
            # Lunch time
            traffic_multiplier = random.uniform(1.1, 1.3)
        else:
            # Normal hours
            traffic_multiplier = random.uniform(0.9, 1.1)
    else:
        # Weekends - generally lighter traffic
        if 10 <= hour <= 18:
            traffic_multiplier = random.uniform(1.0, 1.2)
        else:
            traffic_multiplier = random.uniform(0.8, 1.0)
    
    # Special consideration for Friday afternoon (mosque prayers)
    if day_of_week == 'Friday' and 13 <= hour <= 15:
        traffic_multiplier *= 1.2
    
    # Add some randomness for incidents, weather, etc.
    random_factor = random.uniform(0.95, 1.15)
    traffic_multiplier *= random_factor
    
    duration_in_traffic_minutes = base_duration_minutes * traffic_multiplier
    
    return duration_in_traffic_minutes, traffic_multiplier

def collect_traffic_data():
    """Collect traffic data for predefined Abuja routes using parallel processing"""
    
    all_data_records = []
    current_time = datetime.now()
    
    print(f"\n{'='*80}")
    print(f"Collecting traffic data at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total routes to process: {len(ABUJA_ROUTES)}")
    print(f"Using {MAX_WORKERS} parallel workers")
    print(f"{'='*80}")
    
    # Split routes into batches
    total_routes = len(ABUJA_ROUTES)
    num_batches = math.ceil(total_routes / BATCH_SIZE)
    
    for batch_num in range(num_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min((batch_num + 1) * BATCH_SIZE, total_routes)
        route_batch = ABUJA_ROUTES[start_idx:end_idx]
        
        print(f"\nProcessing batch {batch_num + 1}/{num_batches} ({len(route_batch)} routes)...")
        
        batch_records = process_route_batch(route_batch, current_time)
        all_data_records.extend(batch_records)
        
        # Small delay between batches to be respectful to free API
        if batch_num < num_batches - 1:  # Don't delay after last batch
            time.sleep(1)
    
    print(f"\n✓ Completed processing all {len(ABUJA_ROUTES)} routes")
    print(f"✓ Successfully collected {len(all_data_records)} records")
    
    return all_data_records

def save_to_csv(data_records, filename=CSV_FILENAME):
    """Save collected data to CSV file with thread safety"""
    
    if not data_records:
        print("No data to save.")
        return
    
    df = pd.DataFrame(data_records)
    
    # Use lock to ensure thread-safe file operations
    with file_lock:
        # Check if file exists to append or create new
        if os.path.exists(filename):
            # Append to existing file
            df.to_csv(filename, mode='a', header=False, index=False)
            print(f"✓ Appended {len(data_records)} records to {filename}")
        else:
            # Create new file
            df.to_csv(filename, index=False)
            print(f"✓ Created {filename} with {len(data_records)} records")
        
        # Show total records
        total_records = len(pd.read_csv(filename))
        print(f"Total records in file: {total_records}")
    
    print(f"{'='*80}\n")

def collection_job():
    """Job to be scheduled - collects and saves data"""
    try:
        start_time = time.time()
        data_records = collect_traffic_data()
        save_to_csv(data_records)
        end_time = time.time()
        
        print(f"Collection completed in {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"\n✗ Error in collection job: {str(e)}\n")

def display_statistics():
    """Display current dataset statistics"""
    if os.path.exists(CSV_FILENAME):
        try:
            df = pd.read_csv(CSV_FILENAME)
            print("\n" + "="*80)
            print("CURRENT DATASET STATISTICS")
            print("="*80)
            print(f"Total Records: {len(df)}")
            print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
            print(f"Unique Routes: {df['route_name'].nunique()}")
            print(f"\nTraffic Status Distribution:")
            print(df['traffic_status'].value_counts())
            print("\nAverage Delay by Hour:")
            print(df.groupby('hour')['delay_minutes'].mean().round(2))
            print("="*80 + "\n")
        except Exception as e:
            print(f"Error reading statistics: {e}")

def main():
    """Main function to run continuous data collection"""
    
    print("\n" + "="*80)
    print("ABUJA TRAFFIC DATA COLLECTOR - Enhanced Version")
    print("="*80)
    print(f"Collection Interval: Every {COLLECTION_INTERVAL_MINUTES} minutes")
    print(f"Total Routes: {len(ABUJA_ROUTES)}")
    print(f"Parallel Workers: {MAX_WORKERS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Output File: {CSV_FILENAME}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: OpenStreetMap + Simulated Traffic")
    print("="*80)
    print("\nNote: Traffic conditions are simulated based on typical Abuja patterns")
    print("Press Ctrl+C to stop the collector\n")
    
    # Show existing statistics if file exists
    if os.path.exists(CSV_FILENAME):
        display_statistics()
    
    # Run first collection immediately
    print("Running initial data collection...")
    collection_job()
    
    # Schedule periodic collections
    schedule.every(COLLECTION_INTERVAL_MINUTES).minutes.do(collection_job)
    
    print(f"Scheduled to collect data every {COLLECTION_INTERVAL_MINUTES} minutes.")
    print("Waiting for next collection...\n")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("Data collection stopped by user")
        print("="*80)
        
        # Show final statistics
        if os.path.exists(CSV_FILENAME):
            display_statistics()
        
        print("Goodbye!")

if __name__ == "__main__":
    main()