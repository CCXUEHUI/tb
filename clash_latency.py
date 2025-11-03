import asyncio
import base64
import json
import re
import time
import urllib.parse
import aiohttp

GOOGLE_URL = "https://www.google.com/generate_204"
DOWNLOAD_URL = "https://cachefly.cachefly.net/50mb.test"

def parse_node_url(url):
    try:
        if url.startswith("vmess://"):
            raw = url[8:]
            data = json.loads(base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8"))
            return {"type": "vmess", "server": data["add"]}
        elif url.startswith("trojan://") or url.startswith("vless://"):
            parsed = urllib.parse.urlparse(url)
            return {"type": "other", "server": parsed.hostname}
        elif url.startswith("ss://"):
            return {"type": "ss", "server": "skip"}
    except:
        return None

async def test_google_access(session):
    try:
        start = time.time()
        async with session.get(GOOGLE_URL, timeout=5) as resp:
            if resp.status == 204:
                return int((time.time() - start) * 1000)
    except:
        return None

async def test_download_speed(session):
    try:
        start = time.time()
        async with session.get(DOWNLOAD_URL, timeout=10) as resp:
            total = 0
            async for chunk in resp.content.iter_chunked(1024 * 64):
                total += len(chunk)
        duration = time.time() - start
        speed_mbps = round((total * 8 / 1024 / 1024) / duration, 2)
        return speed_mbps
    except:
        return None

async def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []

    async with aiohttp.ClientSession() as session:
        for line in lines:
            node = parse_node_url(line)
            if not node:
                continue

            google_time = await test_google_access(session)
            download_speed = await test_download_speed(session)

            if google_time is None:
                print(f"❌ 无法访问 Google: {line[:30]}...")
                continue

            print(f"✅ Google: {google_time}ms | DL: {download_speed}Mbps")
            results.append({
                "line": line,
                "google": google_time,
                "speed": download_speed
            })

    # 按 Google 延迟排序
    results.sort(key=lambda x: x["google"])

    with open("v2.txt", "w", encoding="utf-8") as f:
        for item in results:
            f.write(item["line"] + "\n")

    with open("latency.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 写入 {len(results)} 个节点到 v2.txt 和 latency.json")

if __name__ == "__main__":
    asyncio.run(main())
