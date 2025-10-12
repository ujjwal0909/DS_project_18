FROM golang:1.24.8-alpine

RUN apk add --no-cache git protobuf

WORKDIR /app

# Copy module and proto files
COPY ../../proto ./proto
COPY . .

# Initialize and force local replace
RUN go mod init github.com/sifatuddin99289/DS_project_2 || true
RUN go mod edit -replace=github.com/sifatuddin99289/DS_project_2=.
RUN go mod tidy

# Install protoc plugins
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest \
    && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Generate Go files from proto
RUN protoc --go_out=. --go-grpc_out=. proto/telemetry.proto

WORKDIR /app/services/ingestion
RUN go build -o ingestion .

CMD ["./ingestion"]
