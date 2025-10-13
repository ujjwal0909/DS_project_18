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
```
# ===============================
# 1️⃣  Clone your project
# ===============================
cd ~/Desktop
rm -rf My-Distributed-System
git clone https://github.com/Abdullah007noman/My-Distributed-System.git
cd My-Distributed-System

# ===============================
# 2️⃣  Verify Go dependencies
# ===============================
go mod tidy

# ===============================
# 3️⃣  Regenerate proto files (optional safety)
# ===============================
protoc --go_out=. --go-grpc_out=. proto/telemetry.proto

# ===============================
# 4️⃣  Build and launch all services via Docker
# ===============================
docker compose -f compose.grpc.yml down --volumes --remove-orphans
docker compose -f compose.grpc.yml build --no-cache
docker compose -f compose.grpc.yml up -d

# ===============================
# 5️⃣  Confirm all containers are running
# ===============================
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# You should see:
# ingestion (:50051)
# aggregator (:50053)
# alerter (:50054)
# queryapi (:50052)
# redis (:6379)
# timescaledb (:5432 or 55432 depending on port availability)

# ===============================
# 6️⃣  Run your test clients
# ===============================

# (a) Send 5 fake IoT readings
go run client/test_client.go

# (b) Query historical data
go run client/query_client.go

# (c) (Optional) Watch alerts when thresholds are exceeded
# go run client/alert_client.go

# ===============================
# 7️⃣  (Optional) Scale to ≥5 distributed nodes
# ===============================
docker compose -f compose.grpc.yml up -d --scale ingestion=2 --scale aggregator=2

# ===============================
# 8️⃣  Shut down everything cleanly
# ===============================
docker compose -f compose.grpc.yml down --volumes --remove-orphans

```

