# clash_latency.py
# ⚡ 使用 TCP 连接测试订阅节点延迟，并筛选可用节点

import asyncio
import base64
import json
import re
import yaml
import time
from urllib.parse import urlparse, parse_qs

MAX_LATENCY = 600  # 最大延迟阈值（毫秒）

# ✅ 解析 vmess/trojan/vless/ss 节点为标准格式
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
            return {"name": "ss", "type": "ss", "server": "skip", "port": 0}  # 不测速 ss
    except:
        return None

# ✅ 异步 TCP 延迟测试
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

# ✅ 主函数：读取 v2.txt，测速并筛选
async def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    nodes = []
    for line in lines:
        node = parse_node_url(line)
        if node and node["type"] != "ss":
            nodes.append((line, node))

    print(f"📡 待测速节点数: {len(nodes)}")
    good = []

    for line, node in nodes:
        global start_time
        start_time = time.time()
        latency = await test_node_latency(node)
        if latency is not None and latency < MAX_LATENCY:
            print(f"✅ {node['name']} {node['server']}:{node['port']} - {latency}ms")
            good.append(line)
        else:
            print(f"❌ {node['name']} {node['server']}:{node['port']} - 超时或过慢")

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(good) + "\n")
    print(f"✅ 保留 {len(good)} 个节点")

if __name__ == "__main__":
    asyncio.run(main())
