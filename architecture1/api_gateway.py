from flask import Flask, request, jsonify
from database import add_reading, get_latest_readings, get_alerts, get_history
from alerter import process_reading

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200

@app.route('/api/readings', methods=['POST'])
def submit_reading():
    """Receive sensor data"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    sensor_id = data.get('sensor_id')
    sensor_type = data.get('sensor_type')
    value = data.get('value')
    
    if not all([sensor_id, sensor_type, value]):
        return jsonify({'error': 'Missing fields'}), 400
    
    try:
        value = float(value)
        add_reading(sensor_id, sensor_type, value)
        process_reading(sensor_id, sensor_type, value)
        return jsonify({'status': 'OK'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get latest readings"""
    limit = request.args.get('limit', 50, type=int)
    readings = get_latest_readings(limit)
    return jsonify(readings), 200

@app.route('/api/alerts', methods=['GET'])
def get_all_alerts():
    """Get alerts"""
    alerts = get_alerts()
    return jsonify(alerts), 200

@app.route('/api/history/<sensor_id>/<sensor_type>', methods=['GET'])
def get_sensor_history(sensor_id, sensor_type):
    """Get sensor history"""
    history = get_history(sensor_id, sensor_type)
    return jsonify(history), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)