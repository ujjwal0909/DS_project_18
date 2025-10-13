from locust import HttpUser, task, between

class SensorUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def list_sensors(self):
        self.client.get("/api/sensors")

    @task(7)
    def add_reading(self):
        self.client.post("/api/readings",
                         json={"sensor_id": 1, "value": 25.0})
