# DS_project_2
This is the repository for the project 2 of the distributed systems. 

# To execute the architecture-1 (Layered architecture with HTTP), follow the command line
Pull the subfolder with sparse-checkout
```
git clone --no-checkout https://github.com/sifatuddin99289/DS_project_2.git
cd architecture1_layered 
docker compose up -d 
```

# To execute the architecture-2 (microservice with gRPC), follow the command line
Pull the subfolder with sparse-checkout


Clone your project

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
  Regenerate proto files (optional safety)
```
protoc --go_out=. --go-grpc_out=. proto/telemetry.proto
```
 Build and launch all services via Docker
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans
docker compose -f compose.grpc.yml build --no-cache
docker compose -f compose.grpc.yml up -d
```
 Confirm all containers are running
```
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```
 Run your test clients
```
go run client/test_client.go
```
Query historical data
 ```
go run client/query_client.go
```
Shut down everything cleanly
```
docker compose -f compose.grpc.yml down --volumes --remove-orphans

```

