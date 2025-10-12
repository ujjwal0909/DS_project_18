package main
import (
	"fmt"
	"io"
	"log"
	"net"
	"google.golang.org/grpc"
	pb "github.com/Abdullah007noman/My-Distributed-System/proto"
)

type server struct{ pb.UnimplementedIngestionServer }

func (s *server) StreamReadings(stream pb.Ingestion_StreamReadingsServer) error {
	var last uint64
	for {
		r, err := stream.Recv()
		if err == io.EOF {
			return stream.SendAndClose(&pb.IngestAck{LastSeq: last})
		}
		if err != nil {
			return err
		}
		log.Printf("[Ingest] %s T=%.2f H=%.2f", r.SensorId, r.Temperature, r.Humidity)
		last = r.Seq
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil { log.Fatal(err) }
	s := grpc.NewServer()
	pb.RegisterIngestionServer(s, &server{})
	fmt.Println("Ingestion gRPC server listening on :50051")
	log.Fatal(s.Serve(lis))
}
