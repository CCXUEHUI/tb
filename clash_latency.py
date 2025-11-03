# clash_latency.py
# ⚡ 使用 TCP 连接测试订阅节点延迟，并按延迟排序写入 v2.txt

import asyncio
import base64
import json
import re
import time
from urllib.parse import urlparse

MAX_LATENCY = 600  # 最大延迟阈值（毫秒）

def parse_node_url(url):
    try:
        if url.startswith("vmess://"):
            raw = url[8:]
            data = json.loads(base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8"))
            return {
                "name": data.get("ps", "vmess"),
                "type": "vmess",
                "server": data["add"],
                "port": int(data["port"])
            }
        elif url.startswith("trojan://"):
            parsed = urlparse(url)
            return {
                "name": parsed.fragment or "trojan",
                "type": "trojan",
                "server": parsed.hostname,
                "port": parsed.port or 443
            }
        elif url.startswith("vless://"):
            parsed = urlparse(url)
            return {
                "name": parsed.fragment or "vless",
                "type": "vless",
                "server": parsed.hostname,
                "port": parsed.port or 443
            }
        elif url.startswith("ss://"):
            return {"name": "ss", "type": "ss", "server": "skip", "port": 0}
    except:
        return None

async def test_node_latency(node):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(node["server"], node["port"]), timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        return int((time.time() - start_time) * 1000)
    except:
        return None

async def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    nodes = []
    for line in lines:
        node = parse_node_url(line)
        if node and node["type"] != "ss":
            nodes.append((line, node))

    print(f"📡 待测速节点数: {len(nodes)}")
    results = []

    for line, node in nodes:
        global start_time
        start_time = time.time()
        latency = await test_node_latency(node)
        if latency is not None and latency < MAX_LATENCY:
            print(f"✅ {node['name']} {node['server']}:{node['port']} - {latency}ms")
            results.append((line, latency))
        else:
            print(f"❌ {node['name']} {node['server']}:{node['port']} - 超时或过慢")

    # 按延迟升序排序
    results.sort(key=lambda x: x[1])

    with open("v2.txt", "w", encoding="utf-8") as f:
        for line, latency in results:
            f.write(line + f" #latency={latency}\n")

    print(f"✅ 保留 {len(results)} 个节点")

if __name__ == "__main__":
    asyncio.run(main())
