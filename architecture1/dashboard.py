from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Use absolute path to ensure we find the file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, 'sensor_data.json')

def load_data():
    """Load data directly from JSON file"""
    try:
        print(f"Trying to read from: {DATABASE_FILE}")
        if os.path.exists(DATABASE_FILE):
            print(f"File exists! Size: {os.path.getsize(DATABASE_FILE)} bytes")
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                print(f"Loaded {len(data.get('readings', []))} readings")
                return data
        else:
            print(f"File not found at: {DATABASE_FILE}")
    except Exception as e:
        print(f"Error loading data: {e}")
    
    return {'readings': [], 'alerts': []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """Get data for dashboard"""
    try:
        data = load_data()
        readings = data.get('readings', [])
        alerts = data.get('alerts', [])
        
        print(f"Total readings: {len(readings)}, Total alerts: {len(alerts)}")
        
        # Get last 30 readings
        latest_readings = readings[-30:] if len(readings) > 30 else readings
        
        # Reverse to show newest first
        latest_readings = list(reversed(latest_readings))
        
        # Calculate averages
        temps = [r['value'] for r in readings if r.get('sensor_type') == 'temperature']
        humids = [r['value'] for r in readings if r.get('sensor_type') == 'humidity']
        
        temp_avg = sum(temps) / len(temps) if temps else 0
        humid_avg = sum(humids) / len(humids) if humids else 0
        
        print(f"Temp avg: {temp_avg}, Humid avg: {humid_avg}")
        
        # Get recent alerts (last 10)
        recent_alerts = alerts[-10:] if len(alerts) > 10 else alerts
        recent_alerts = list(reversed(recent_alerts))
        
        result = {
            'readings': latest_readings,
            'alerts': recent_alerts,
            'temp_avg': round(temp_avg, 2),
            'humid_avg': round(humid_avg, 2),
            'alert_count': len(recent_alerts)
        }
        
        print(f"Returning: {len(result['readings'])} readings, {len(result['alerts'])} alerts")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"ERROR in get_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'readings': [],
            'alerts': [],
            'temp_avg': 0,
            'humid_avg': 0,
            'alert_count': 0
        }), 500

if __name__ == '__main__':
    print("="*60)
    print("Starting IoT Dashboard")
    print("="*60)
    print(f"Database file: {DATABASE_FILE}")
    print(f"File exists: {os.path.exists(DATABASE_FILE)}")
    if os.path.exists(DATABASE_FILE):
        print(f"File size: {os.path.getsize(DATABASE_FILE)} bytes")
    print("="*60)
    print("Dashboard running at: http://localhost:5001")
    print("="*60)
    app.run(host='127.0.0.1', port=5001, debug=True)