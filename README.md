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

## Consensus algorithms (2PC and Raft)

The `consensus/` directory contains a lightweight reference implementation of
the assignment requirements. The solution simulates gRPC-style interactions
using a minimal JSON-over-TCP RPC layer so it can run in restricted execution
environments. Each node exposes the following capabilities:

* Voting and decision phases of the two-phase commit protocol.
* Leader election and log replication for a simplified Raft cluster.
* A CLI entrypoint (`python -m consensus.run_node`) for starting a node.
* A comprehensive pytest suite covering five Raft scenarios plus 2PC abort
  behaviour.

### Running the test suite

```
cd consensus
pytest
```

### Starting a local cluster

```
python -m consensus.run_node n1 127.0.0.1 5600 --peers '{"n2": "127.0.0.1:5601", "n3": "127.0.0.1:5602"}'
```

Start additional nodes with matching peer maps. Once the nodes are running you
can execute two-phase commit transactions and Raft client commands using the
`consensus.tests.test_consensus.Cluster` helper as a reference.
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
