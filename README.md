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
rm -rf ds_tmp
git clone --no-checkout https://github.com/sifatuddin99289/DS_project_2.git ds_tmp
cd ds_tmp
git sparse-checkout init --cone
git sparse-checkout set architecture2
git checkout
cd architecture2
```
Clean previous containers (if any)
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans
```
Build and Run the gRPC Microservice Architecture
```
# Ensure Docker is running
docker compose -f compose.grpc.yml up -d --build
```
Run your gRPC clients
```
# To confirm they’re running
docker ps
```
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
Performance analysis
```
python3 benchmark_grpc.py

```
Clean shutdown when done
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans
```
