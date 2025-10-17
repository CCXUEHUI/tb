import re
import json
import base64
import urllib.parse
import requests
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

def test_google_speed(proxy_url):
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    try:
        start = time.time()
        r = requests.get("https://www.google.com/generate_204", proxies=proxies, timeout=5)
        if r.status_code == 204:
            return round((time.time() - start) * 1000, 2)
    except:
        pass
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

def build_proxy_url(config):
    if config.startswith("vmess://"):
        return None  # vmess 需特殊客户端支持，无法直接代理
    elif config.startswith("vless://"):
        return None  # 同上
    elif config.startswith("trojan://"):
        match = re.search(r'trojan://([^@]+)@([^:]+):(\d+)', config)
        if match:
            host = match.group(2)
            port = match.group(3)
            return f"http://{host}:{port}"
    elif config.startswith("ss://"):
        match = re.search(r'@([^:]+):(\d+)', config)
        if match:
            host = match.group(1)
            port = match.group(2)
            return f"http://{host}:{port}"
    return None

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for config in lines:
        ip, port = extract_ip_port(config)
        if not ip or not port:
            continue
        city = get_city_cn(ip)
        proxy = build_proxy_url(config)
        if proxy:
            delay = test_google_speed(proxy)
        else:
            delay = float('inf')
        results.append((delay, config, city))

    top = sorted(results, key=lambda x: x[0])[:20]

    with open("v2.txt", "w", encoding="utf-8") as f:
        for i, (delay, config, city) in enumerate(top, 1):
            f.write(format_config(config, i, city) + "\n")

if __name__ == "__main__":
    main()
