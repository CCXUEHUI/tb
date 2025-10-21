import re
import json
import base64
import urllib.parse
import requests

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
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    enriched = []
    for config in lines:
        ip, port = extract_ip_port(config)
        city = get_city_cn(ip) if ip else "未知"
        enriched.append((city, config))

    # 按城市名排序（中文拼音顺序）
    enriched.sort(key=lambda x: x[0])

    with open("v2.txt", "w", encoding="utf-8") as f:
        for i, (city, config) in enumerate(enriched, 1):
            f.write(format_config(config, i, city) + "\n")

if __name__ == "__main__":
    main()
