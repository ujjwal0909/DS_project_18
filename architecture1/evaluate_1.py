import time
import statistics
import requests
import concurrent.futures

# ------------------------------------
# Configuration
# ------------------------------------
URL = "http://localhost:8000/api/readings/latest"   # endpoint to test
NUM_REQUESTS = 200                                  # total requests
CONCURRENCY = 20                                    # number of parallel threads

# ------------------------------------
# Worker function
# ------------------------------------
def fetch(_):
    start = time.time()
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Error:", e)
        return None
    latency = time.time() - start
    return latency

# ------------------------------------
# Run test
# ------------------------------------
def run_test():
    latencies = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        for latency in executor.map(fetch, range(NUM_REQUESTS)):
            if latency is not None:
                latencies.append(latency)

    duration = time.time() - start_time
    throughput = len(latencies) / duration

    if not latencies:
        print("No successful responses.")
        return

    print(f"\n✅ Completed {len(latencies)} requests")
    print(f"Throughput: {throughput:.2f} requests/sec")
    print(f"Average latency: {statistics.mean(latencies)*1000:.2f} ms")
    print(f"P90 latency: {statistics.quantiles(latencies, n=10)[8]*1000:.2f} ms")
    print(f"P99 latency: {max(latencies)*1000:.2f} ms")


    import matplotlib.pyplot as plt

    plt.hist([l*1000 for l in latencies], bins=20, color='skyblue')
    plt.xlabel("Latency (ms)")
    plt.ylabel("Count")
    plt.title("Latency distribution for 200 requests")
    plt.show()


if __name__ == "__main__":
    run_test()
