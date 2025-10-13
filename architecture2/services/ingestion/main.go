package main

import (
	"io"
	"log"
	"net"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
	"google.golang.org/grpc"

	pb "github.com/Abdullah007noman/My-Distributed-System/proto"
)

type server struct {
	pb.UnimplementedIngestionServer
	rdb *redis.Client
}

func newServer() *server {
	addr := os.Getenv("REDIS_ADDR")
	if addr == "" {
		addr = "redis:6379"
	}
	return &server{
		rdb: redis.NewClient(&redis.Options{Addr: addr}),
	}
}

func (s *server) StreamReadings(stream pb.Ingestion_StreamReadingsServer) error {
	ctx := stream.Context()
	var last uint64
	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			return stream.SendAndClose(&pb.IngestAck{LastSeq: last})
		}
		if err != nil {
			return err
		}
		last = msg.Seq
		// Push to Redis stream for downstream processing
		_, err = s.rdb.XAdd(ctx, &redis.XAddArgs{
			Stream: "readings",
			Values: map[string]interface{}{
				"sensor_id":   msg.SensorId,
				"site":        msg.Site,
				"ts_unix_ms":  msg.TsUnixMs,
				"temperature": msg.Temperature,
				"humidity":    msg.Humidity,
				"seq":         msg.Seq,
			},
		}).Result()
		if err != nil {
			log.Printf("redis xadd error: %v", err)
		}
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatal(err)
	}
	s := grpc.NewServer()
	pb.RegisterIngestionServer(s, newServer())
	log.Println("Ingestion gRPC listening on :50051")
	if err := s.Serve(lis); err != nil {
		log.Fatal(err)
	}
	_ = time.Now()
}
