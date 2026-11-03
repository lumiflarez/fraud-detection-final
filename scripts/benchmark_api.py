"""Latency benchmark for the fraud API: N sequential /predict requests, p50/p95 in ms."""
import argparse
import json
import statistics
import time
import httpx

ROW = {f"f{i}": v for i, v in enumerate([0.1, -0.2, 0.3, 0.0, 0.1, 0.2, 0.0, 0.1, 0.2, 0.0])}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8082")
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--output", default="docs/week7/latency-onnx.json")
    a = p.parse_args()
    with httpx.Client(base_url=a.url, timeout=10.0) as c:
        for _ in range(a.warmup):
            c.post("/predict", json=ROW).raise_for_status()
        lat = []
        for _ in range(a.n):
            t0 = time.perf_counter()
            c.post("/predict", json=ROW).raise_for_status()
            lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    result = {"url": a.url, "requests": a.n, "warmup": a.warmup,
              "p50_ms": round(statistics.median(lat), 2),
              "p95_ms": round(lat[int(len(lat) * 0.95) - 1], 2),
              "max_ms": round(lat[-1], 2),
              "note": "sequential requests through kubectl port-forward; includes tunnel overhead"}
    json.dump(result, open(a.output, "w"), indent=2)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
