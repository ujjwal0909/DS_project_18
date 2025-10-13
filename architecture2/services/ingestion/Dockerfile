FROM golang:1.24.8-alpine
RUN apk add --no-cache git
WORKDIR /app
# bring in module files first for better caching
COPY go.mod go.sum ./
RUN go mod download
# bring in proto and this service's code
COPY proto ./proto
COPY services/ingestion/ .
RUN go mod tidy
RUN go build -o ingestion .
EXPOSE 50051
CMD ["./ingestion"]
