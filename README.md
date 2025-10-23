# DS Project – Consensus Algorithms
This repository now tracks the follow-on consensus-algorithms assignment that extends
the previous distributed-systems projects. In addition to the execution instructions
for the two existing architectures, the assignment requires a set of
implementations that exercise both Two-Phase Commit (2PC) and Raft.

## Project Overview
The overarching goal is to provide hands-on experience with consensus algorithms
by implementing simplified versions of 2PC and Raft on top of existing
distributed-system architectures. Implementations must use gRPC for inter-process
communication and Docker for containerization. The expected workload is roughly
three weeks, so plan accordingly.

### Q0. Bid on Three Implementations
Select three existing implementations (developed by other teams for Project 2) to
extend. Each choice must be distinct and may be claimed by at most three teams.
Use the instructor-provided spreadsheet to register the selections.

### Q1. Two-Phase Commit – Voting Phase (~0.5 week)
Implement the voting phase of 2PC on one of the selected implementations. Define
custom gRPC messages and RPCs, containerize each node, and demonstrate that at
least five containers can communicate. The coordinator must issue vote requests
and participants respond with commit or abort votes.

### Q2. Two-Phase Commit – Decision Phase (~0.5 week)
Extend the same implementation with the 2PC decision phase. The coordinator must
collect votes and broadcast global commit/abort decisions. Participants should
block waiting for the coordinator’s decision and then apply the outcome. The
voting and decision phases may be implemented in different languages, but they
must still communicate via gRPC using the same proto definitions. Log the required
client/server RPC messages for both phases, and continue to support at least five
communicating containers.

### Q3. Raft – Leader Election (~0.5 week)
Implement a simplified Raft leader election on one of the remaining selected
implementations. Start all processes as followers with a 1-second heartbeat
timeout and randomized election timeout between 1.5 and 3 seconds. Upon timeout,
a follower becomes a candidate, increments its term, votes for itself, and issues
`RequestVote` RPCs. A candidate that gains a majority becomes leader and starts
sending heartbeat `AppendEntries` RPCs. Log the client and server RPC messages as
specified and containerize at least five communicating nodes.

### Q4. Raft – Log Replication (~0.5 week)
Build log replication on top of the leader election implementation. Each node
maintains a log of committed and pending operations. The leader appends new
client requests to its log, propagates the entire log (and the latest committed
index) via heartbeats, and commits operations after receiving majority
acknowledgements. Followers mirror the leader’s log, ensure committed entries are
executed, and send acknowledgements back. Clients may contact any node, which
must forward requests to the leader. Continue to log RPC calls and maintain the
five-node container setup.

### Q5. Raft Test Cases (~0.5 week)
Design and implement five distinct test cases for the Raft implementation. Each
test should be documented, and execution evidence (e.g., screenshots) must be
included in the final report. Consider scenarios such as new nodes joining the
cluster, leader failure, log divergence, and recovery.

### Deliverables
* Source code for the 2PC and Raft implementations.
* Docker artifacts enabling multi-node communication.
* A README explaining build/run steps, unusual behavior, and referenced sources.
* A report listing team members, contributions, test documentation, and
  execution evidence. Include the repository link in both README and report.
* Be aware of the late penalty: 20 points per day.

The remaining sections document how to run the previously delivered
architectures.

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
