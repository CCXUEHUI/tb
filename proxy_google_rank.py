import requests
import time
import json

CLASH_API = "http://127.0.0.1:9090"
PROXY = "http://127.0.0.1:7890"
TARGET = "https://www.google.com/generate_204"

def get_proxies():
    resp = requests.get(f"{CLASH_API}/proxies")
    proxies = resp.json()["proxies"]
    return [name for name in proxies if name not in ["DIRECT", "REJECT", "GLOBAL"]]

def switch_proxy(name):
    requests.put(f"{CLASH_API}/proxies/GLOBAL", json={"name": name})

def test_latency():
    try:
        start = time.time()
        resp = requests.get(TARGET, proxies={"http": PROXY, "https": PROXY}, timeout=10)
        if resp.status_code == 204:
            return round((time.time() - start) * 1000)
    except:
        return None

def main():
    results = []
    proxies = get_proxies()
    for name in proxies:
        print(f"⏱️ 测试节点: {name}")
        switch_proxy(name)
        time.sleep(2)
        latency = test_latency()
        results.append({"name": name, "latency_ms": latency if latency else "timeout"})

    results.sort(key=lambda x: x["latency_ms"] if isinstance(x["latency_ms"], int) else 9999)

    with open("proxy_rank.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open("proxy_rank.md", "w", encoding="utf-8") as f:
        f.write("| 节点名称 | Google延迟 |\n|---|---|\n")
        for r in results:
            f.write(f"| {r['name']} | {r['latency_ms']}ms |\n")

    print("✅ 排行榜已生成：proxy_rank.json / proxy_rank.md")

if __name__ == "__main__":
    main()
