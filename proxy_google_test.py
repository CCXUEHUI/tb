import subprocess
import json
import time

PROXY = "http://127.0.0.1:7890"
TARGET = "https://www.google.com/generate_204"

def test_google_via_proxy():
    try:
        start = time.time()
        result = subprocess.run(
            ["curl", "-x", PROXY, "-o", "/dev/null", "-s", "-w", "%{time_total}", TARGET],
            capture_output=True, text=True, timeout=10
        )
        duration = float(result.stdout.strip())
        return round(duration * 1000)
    except Exception:
        return None

def main():
    latency = test_google_via_proxy()
    output = {
        "proxy": PROXY,
        "target": TARGET,
        "google_latency_ms": latency if latency is not None else "timeout"
    }

    with open("proxy_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ Google 访问延迟: {output['google_latency_ms']}ms")

if __name__ == "__main__":
    main()
