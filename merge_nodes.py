import re
import base64
import json
import socket
import requests
from urllib.parse import urlparse

def extract_google(text):
    match = re.search(r'#google=(\d+)', text)
    return f"G({match.group(1)}ms)" if match else "G(?)"

def extract_speed(text):
    match = re.search(r'#speed=([\d.]+)', text)
    return f"D({match.group(1)}Mbps)" if match else "D(?)"

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

def clean_and_rename(line):
    g = extract_google(line)
    d = extract_speed(line)

    if line.startswith("vmess://"):
        try:
            raw = line[8:]
            city = get_city_from_vmess(raw)
            decoded = base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8")
            data = json.loads(decoded)
            data["ps"] = f"{city}-{g}-{d}"
            new_raw = base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode().rstrip("=")
            return f"vmess://{new_raw}"
        except:
            return line
    elif line.startswith("vless://") or line.startswith("trojan://"):
        try:
            url = line.split("#")[0]
            city = get_city_from_url(line)
            return f"{url}#{city}-{g}-{d}"
        except:
            return line
    else:
        return line

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    renamed = [clean_and_rename(line) for line in lines]

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed) + "\n")

if __name__ == "__main__":
    main()
