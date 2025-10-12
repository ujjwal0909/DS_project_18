import json
import os
from datetime import datetime
import threading

DATABASE_FILE = 'sensor_data.json'

# Lock to prevent concurrent writes
file_lock = threading.Lock()

def init_database():
    """Create database file if it doesn't exist"""
    if not os.path.exists(DATABASE_FILE):
        with file_lock:
            with open(DATABASE_FILE, 'w') as f:
                json.dump({
                    'readings': [],
                    'alerts': []
                }, f)

def load_data():
    """Load all data from file"""
    init_database()
    with file_lock:
        try:
            with open(DATABASE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, reset it
            print("Warning: Corrupted JSON file detected. Resetting...")
            return {'readings': [], 'alerts': []}

def save_data(data):
    """Save all data to file"""
    with file_lock:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

def add_reading(sensor_id, sensor_type, value):
    """Add a new sensor reading"""
    with file_lock:
        data = load_data()
        data['readings'].append({
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        save_data(data)

def get_latest_readings(limit=50):
    """Get last N readings"""
    data = load_data()
    return data['readings'][-limit:]

def add_alert(sensor_id, sensor_type, message):
    """Add an alert"""
    with file_lock:
        data = load_data()
        data['alerts'].append({
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        save_data(data)

def get_alerts():
    """Get all alerts from last hour"""
    data = load_data()
    return data['alerts'][-20:]

def get_history(sensor_id, sensor_type):
    """Get all readings for a sensor"""
    data = load_data()
    return [r for r in data['readings'] 
            if r['sensor_id'] == sensor_id and r['sensor_type'] == sensor_type]