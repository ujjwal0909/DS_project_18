# DS_project_2
This is the repository for the project 2 of the distributed systems. 

## To execute the architecture-1 (Layered architecture with HTTP), follow the command line
Pull the subfolder with sparse-checkout
```
git clone --no-checkout https://github.com/sifatuddin99289/DS_project_2.git
cd architecture1
docker compose down -v
docker compose up -d --build

```
## For the evaluation part run the evaluate_1.py scripts in the project directory: 

```
python evaluate_1.py

```

## To execute the architecture-2 (microservice with gRPC), follow the command line
Pull the subfolder with sparse-checkout


Clone the repository
```
cd ~/Desktop
rm -rf DS_project_2
git clone https://github.com/sifatuddin99289/DS_project_2.git
cd DS_project_2/architecture2
```
 Verify Go dependencies
```
go mod tidy
```
Regenerate protobuf stubs
```
protoc --go_out=. --go-grpc_out=. proto/telemetry.proto
```
Clean previous containers (if any)
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans
```
Build all Dockerized microservices
```
docker compose -f compose.grpc.yml build --no-cache
```
Launch the full distributed stack
```
docker compose -f compose.grpc.yml up -d
```
Confirm all nodes are running
```
docker compose -f compose.grpc.yml ps
```

Run your gRPC clients

Send 5 fake IoT sensor readings
```
go run client/test_client.go
```
Query historical sensor data
```
go run client/query_client.go
```
Watch alerts for high temperatures
```
go run client/alert_client.go
```
Access Grafana dashboard (visualization)
```
# Open in your browser:
# 👉 http://localhost:3000
# Login:  admin / admin
# Add a PostgreSQL datasource:
#   Host: timescaledb:5432
#   Database: postgres
#   User: postgres
#   Password: postgres
# Create a dashboard to plot temperature & humidity vs time.
```
Clean shutdown when done
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans
```
