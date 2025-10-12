from config import TEMP_HIGH, TEMP_LOW, HUMIDITY_HIGH, HUMIDITY_LOW
from database import add_alert

def check_temperature_alert(sensor_id, value):
    """Check if temperature is out of range"""
    if value > TEMP_HIGH:
        add_alert(sensor_id, 'temperature', f'🚨 TOO HIGH: {value}°C (threshold: {TEMP_HIGH}°C)')
    elif value < TEMP_LOW:
        add_alert(sensor_id, 'temperature', f'🚨 TOO LOW: {value}°C (threshold: {TEMP_LOW}°C)')

def check_humidity_alert(sensor_id, value):
    """Check if humidity is out of range"""
    if value > HUMIDITY_HIGH:
        add_alert(sensor_id, 'humidity', f'🚨 TOO HIGH: {value}% (threshold: {HUMIDITY_HIGH}%)')
    elif value < HUMIDITY_LOW:
        add_alert(sensor_id, 'humidity', f'🚨 TOO LOW: {value}% (threshold: {HUMIDITY_LOW}%)')

def process_reading(sensor_id, sensor_type, value):
    """Process a reading and check for alerts"""
    if sensor_type == 'temperature':
        check_temperature_alert(sensor_id, value)
    elif sensor_type == 'humidity':
        check_humidity_alert(sensor_id, value)