import re
import base64
import json
import socket
import requests
from urllib.parse import urlparse

def resolve_ip(host):
    try:
        return socket.gethostbyname(host)
    except:
        return None

def ip_to_city(ip):
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = resp.json()
        if data.get("status") == "success":
            return data.get("city") or data.get("regionName") or data.get("country")
    except:
        pass
    return "未知"

def get_city_from_vmess(raw):
    try:
        decoded = base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8")
        data = json.loads(decoded)
        host = data.get("add", "")
        ip = resolve_ip(host)
        return ip_to_city(ip)
    except:
        return "未知"

def get_city_from_url(url):
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        ip = resolve_ip(host)
        return ip_to_city(ip)
    except:
        return "未知"

def rename(line, ping, speed):
    label = f"P({ping}ms)-D({speed}Mbps)"
    if line.startswith("vmess://"):
        try:
            raw = line[8:]
            city = get_city_from_vmess(raw)
            decoded = base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8")
            data = json.loads(decoded)
            data["ps"] = f"{city}-{label}"
            new_raw = base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode().rstrip("=")
            return f"vmess://{new_raw}"
        except:
            return line
    elif line.startswith("vless://") or line.startswith("trojan://"):
        try:
            url = line.split("#")[0]
            city = get_city_from_url(line)
            return f"{url}#{city}-{label}"
        except:
            return line
    else:
        return line

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with open("latency.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    line_map = {item["line"]: item for item in data}
    renamed = []

    for line in lines:
        item = line_map.get(line)
        if item:
            renamed.append(rename(line, item["ping"], item["speed"]))
        else:
            renamed.append(line)

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed) + "\n")

if __name__ == "__main__":
    main()
