import re
import json
import base64
import urllib.parse
import requests
import socket
import time

def extract_ip_port(config):
    try:
        if config.startswith("vmess://"):
            data = json.loads(base64.b64decode(config[8:] + '==').decode("utf-8"))
            return data.get("add"), int(data.get("port"))
        elif config.startswith(("vless://", "trojan://", "ss://")):
            match = re.search(r'@([\w\.-]+):(\d+)', config)
            if match:
                return match.group(1), int(match.group(2))
    except:
        pass
    return None, None

def get_city_cn(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=city&lang=zh-CN", timeout=5)
        if r.status_code == 200:
            return r.json().get("city", "未知")
    except:
        pass
    return "未知"

def test_tcp(ip, port):
    try:
        start = time.time()
        with socket.create_connection((ip, port), timeout=3):
            return round((time.time() - start) * 1000, 2)  # 毫秒
    except:
        return float('inf')

def format_config(config, index, city):
    label = f"{str(index).zfill(2)}-{city}"
    if config.startswith("vmess://"):
        try:
            data = json.loads(base64.b64decode(config[8:] + '==').decode("utf-8"))
            data["ps"] = label
            new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            return "vmess://" + base64.b64encode(new_json.encode("utf-8")).decode("utf-8")
        except:
            return config
    else:
        parts = config.split("#", 1)
        base = parts[0]
        return f"{base}#{urllib.parse.quote(label)}"

def main():
    with open("v2_raw.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for config in lines:
        ip, port = extract_ip_port(config)
        if not ip or not port:
            continue
        delay = test_tcp(ip, port)
        city = get_city_cn(ip)
        results.append((delay, config, city))

    # 排序并选出最快的前 20 个
    top = sorted(results, key=lambda x: x[0])[:20]

    with open("v2.txt", "w", encoding="utf-8") as f:
        for i, (delay, config, city) in enumerate(top, 1):
            f.write(format_config(config, i, city) + "\n")

if __name__ == "__main__":
    main()
