import requests
import random
import time

def simulate_sensor(sensor_id, sensor_type, api_url='http://127.0.0.1:5000'):
    """Simulate one sensor sending data"""
    while True:
        try:
            # Generate random value
            if sensor_type == 'temperature':
                value = random.uniform(15, 35)  # Normal: 15-35°C
                if random.random() < 0.1:  # 10% chance of alert
                    value = random.choice([random.uniform(-5, 5), random.uniform(35, 40)])
            else:  # humidity
                value = random.uniform(30, 70)  # Normal: 30-70%
                if random.random() < 0.1:
                    value = random.choice([random.uniform(0, 15), random.uniform(80, 100)])
            
            # Send to API
            data = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'value': round(value, 2)
            }
            
            response = requests.post(f'{api_url}/api/readings', json=data, timeout=5)
            
            if response.status_code == 201:
                print(f'✓ {sensor_id}: {data["value"]}')
            else:
                print(f'✗ {sensor_id}: HTTP {response.status_code}')
                
        except requests.exceptions.Timeout:
            print(f'✗ {sensor_id}: Timeout')
        except requests.exceptions.ConnectionError:
            print(f'✗ {sensor_id}: Cannot connect to {api_url}')
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f'✗ {sensor_id}: Error - {e}')
        
        time.sleep(3)  # Send every 3 seconds

if __name__ == '__main__':
    import threading
    
    sensors = [
        ('sensor_001', 'temperature'),
        ('sensor_002', 'temperature'),
        ('sensor_003', 'humidity'),
        ('sensor_004', 'humidity'),
        ('sensor_005', 'temperature'),
    ]
    
    print("Starting 5 sensors...")
    print("Connecting to API at http://127.0.0.1:5000")
    
    for sensor_id, sensor_type in sensors:
        t = threading.Thread(target=simulate_sensor, args=(sensor_id, sensor_type), daemon=True)
        t.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping sensors...")