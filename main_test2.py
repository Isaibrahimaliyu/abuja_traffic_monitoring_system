
from flask import Flask, jsonify, send_file, render_template

import requests
import pandas as pd
from datetime import datetime
import time
import os
import random
import concurrent.futures
from threading import Lock
import math

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# ORIGINAL CONFIGURATION
# =========================
CSV_FILENAME = 'abuja_traffic_data.csv'
MAX_WORKERS = 5
BATCH_SIZE = 20
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving/"

file_lock = Lock()


# =========================

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# ORIGINAL ROUTES (UNCHANGED)
# =========================
ABUJA_ROUTES = [
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

# 🔹 You can paste back ALL your routes here without issues

# =========================
# ORIGINAL FUNCTIONS
# =========================
def generate_statistics():
    if not os.path.exists(CSV_FILENAME):
        return None

    df = pd.read_csv("C:\\Users\\USER\\OneDrive\\Documents\\traffic model\\abuja_traffic_data.csv")

    stats = {
        "total_records": len(df),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "unique_routes": df['route_name'].nunique(),
        "traffic_distribution": df['traffic_status'].value_counts().to_dict(),
        "avg_delay_by_hour": df.groupby('hour')['delay_minutes'].mean().round(2).to_dict()
    }

    return stats

def get_route_info(origin_coords, destination_coords):
    coords = f"{origin_coords[0]},{origin_coords[1]};{destination_coords[0]},{destination_coords[1]}"
    url = f"{OSRM_BASE_URL}{coords}?overview=false"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                return route['distance'], route['duration']
    except Exception as e:
        print("Error fetching route:", e)

    return None, None


def simulate_traffic_conditions(hour, day_of_week, base_duration_minutes):
    traffic_multiplier = random.uniform(0.9, 1.1)

    if day_of_week not in ['Saturday', 'Sunday']:
        if 7 <= hour <= 9:
            traffic_multiplier = random.uniform(1.3, 1.8)
        elif 17 <= hour <= 19:
            traffic_multiplier = random.uniform(1.5, 2.0)

    duration = base_duration_minutes * traffic_multiplier
    return duration, traffic_multiplier


def process_route(route, current_time):
    origin, destination, route_name, origin_name, dest_name = route

    distance_m, duration_s = get_route_info(origin, destination)
    if not distance_m:
        return None

    base_minutes = duration_s / 60
    traffic_minutes, multiplier = simulate_traffic_conditions(
        current_time.hour,
        current_time.strftime('%A'),
        base_minutes
    )

    delay = traffic_minutes - base_minutes

    if delay < 5:
        status = "No Traffic"
    elif delay < 15:
        status = "Light Traffic"
    elif delay < 30:
        status = "Moderate Traffic"
    else:
        status = "Heavy Traffic"

    return {
        "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "route_name": route_name,
        "origin": origin_name,
        "destination": dest_name,
        "distance_km": round(distance_m / 1000, 2),
        "duration_minutes": round(base_minutes, 2),
        "duration_in_traffic_minutes": round(traffic_minutes, 2),
        "delay_minutes": round(delay, 2),
        "traffic_status": status,
        "traffic_multiplier": round(multiplier, 2)
    }


def collect_traffic_data():
    records = []
    now = datetime.now()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_route, r, now) for r in ABUJA_ROUTES]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                records.append(result)

    return records


def save_to_csv(data_records):
    if not data_records:
        return 0

    df = pd.DataFrame(data_records)

    with file_lock:
        if os.path.exists(CSV_FILENAME):
            df.to_csv(CSV_FILENAME, mode='a', header=False, index=False)
        else:
            df.to_csv(CSV_FILENAME, index=False)

    return len(data_records)

# =========================
# FLASK ENDPOINTS
# =========================
@app.route("/")
def home():
    return render_template(
        "index.html",
        routes=len(ABUJA_ROUTES)
    )



@app.route("/collect", methods=["GET"])
def collect():
    data = collect_traffic_data()
    saved = save_to_csv(data)

    return jsonify({
        "status": "success",
        "records_saved": saved
    })


@app.route("/data", methods=["GET"])
def data():
    if not os.path.exists(CSV_FILENAME):
        return jsonify({"message": "No data collected yet"}), 404

    df = pd.read_csv(CSV_FILENAME)
    


@app.route("/routes", methods=["GET"])
def routes():
    return jsonify([
        {
            "route_name": r[2],
            "origin": r[3],
            "destination": r[4]
        } for r in ABUJA_ROUTES
    ])


@app.route("/download", methods=["GET"])
def download():
    if not os.path.exists(CSV_FILENAME):
        return jsonify({"message": "CSV file not found"}), 404

    return send_file(CSV_FILENAME, as_attachment=True)

# =========================
# RUN FLASK SERVER
# =========================
if __name__ == "__main__":
 app.run(debug=True)

# 🔹 You can paste back ALL your routes here without issues

# =========================
# ORIGINAL FUNCTIONS
# =========================
def get_route_info(origin_coords, destination_coords):
    coords = f"{origin_coords[0]},{origin_coords[1]};{destination_coords[0]},{destination_coords[1]}"
    url = f"{OSRM_BASE_URL}{coords}?overview=false"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                return route['distance'], route['duration']
    except Exception as e:
        print("Error fetching route:", e)

    return None, None


def simulate_traffic_conditions(hour, day_of_week, base_duration_minutes):
    traffic_multiplier = random.uniform(0.9, 1.1)

    if day_of_week not in ['Saturday', 'Sunday']:
        if 7 <= hour <= 9:
            traffic_multiplier = random.uniform(1.3, 1.8)
        elif 17 <= hour <= 19:
            traffic_multiplier = random.uniform(1.5, 2.0)

    duration = base_duration_minutes * traffic_multiplier
    return duration, traffic_multiplier


def process_route(route, current_time):
    origin, destination, route_name, origin_name, dest_name = route

    distance_m, duration_s = get_route_info(origin, destination)
    if not distance_m:
        return None

    base_minutes = duration_s / 60
    traffic_minutes, multiplier = simulate_traffic_conditions(
        current_time.hour,
        current_time.strftime('%A'),
        base_minutes
    )

    delay = traffic_minutes - base_minutes

    if delay < 5:
        status = "No Traffic"
    elif delay < 15:
        status = "Light Traffic"
    elif delay < 30:
        status = "Moderate Traffic"
    else:
        status = "Heavy Traffic"

    return {
        "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "route_name": route_name,
        "origin": origin_name,
        "destination": dest_name,
        "distance_km": round(distance_m / 1000, 2),
        "duration_minutes": round(base_minutes, 2),
        "duration_in_traffic_minutes": round(traffic_minutes, 2),
        "delay_minutes": round(delay, 2),
        "traffic_status": status,
        "traffic_multiplier": round(multiplier, 2)
    }

def collect_traffic_data():
    records = []
    now = datetime.now()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_route, r, now) for r in ABUJA_ROUTES]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                records.append(result)

    return records


def save_to_csv(data_records):
    if not data_records:
        return 0

    df = pd.DataFrame(data_records)

    with file_lock:
        if os.path.exists(CSV_FILENAME):
            df.to_csv(CSV_FILENAME, mode='a', header=False, index=False)
        else:
            df.to_csv(CSV_FILENAME, index=False)

    return len(data_records)

# =========================
# FLASK ENDPOINTS
# =========================
@app.route("/")
def home():
    return jsonify({
       "message": "Abuja Traffic Data API (Flask Applied)",
        "routes": len(ABUJA_ROUTES),
        "endpoints": ["/collect", "/data", "/routes", "/download"]
    })


@app.route("/collect", methods=["GET"])
def collect():
    data = collect_traffic_data()
    saved = save_to_csv(data)

    return jsonify({
        "status": "success",
        "records_saved": saved
    })


@app.route("/data", methods=["GET"])
def data():
    if not os.path.exists(CSV_FILENAME):
        return jsonify({"message": "No data collected yet"}), 404

    df = pd.read_csv(CSV_FILENAME)
    return df.tail(100).to_json(orient="records")


@app.route("/data")
def data():
    if not os.path.exists(CSV_FILENAME):
        return "No traffic data available yet."

    df = pd.read_csv(CSV_FILENAME)

    # Show recent records only (cleaner)
    df = df.tail(100)

    return render_template(
        "data.html",
        tables=[df.to_html(classes="table", index=False)],
        total_records=len(df)
    )


@app.route("/download", methods=["GET"])
def download():
    if not os.path.exists(CSV_FILENAME):
        return jsonify({"message": "CSV file not found"}), 404

    return send_file(CSV_FILENAME, as_attachment=True)

# =========================
# RUN FLASK SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
