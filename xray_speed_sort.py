import json
import base64
import urllib.parse
import requests
import subprocess
import re

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

def build_xray_config(nodes):
    outbounds = []
    for i, line in enumerate(nodes):
        tag = f"node{i}"
        if line.startswith("vmess://"):
            try:
                data = json.loads(base64.b64decode(line[8:] + '==').decode("utf-8"))
                outbounds.append({
                    "tag": tag,
                    "protocol": "vmess",
                    "settings": {
                        "vnext": [{
                            "address": data["add"],
                            "port": int(data["port"]),
                            "users": [{
                                "id": data["id"],
                                "alterId": int(data.get("aid", 0)),
                                "security": data.get("scy", "auto")
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": data.get("net", "tcp"),
                        "security": "tls" if data.get("tls") == "tls" else "none",
                        "wsSettings": {
                            "path": data.get("path", ""),
                            "headers": {
                                "Host": data.get("host", "")
                            }
                        } if data.get("net") == "ws" else None
                    }
                })
            except:
                continue
        elif line.startswith("vless://"):
            match = re.match(r'vless://([^@]+)@([^:]+):(\d+)', line)
            if match:
                uuid, host, port = match.groups()
                outbounds.append({
                    "tag": tag,
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": host,
                            "port": int(port),
                            "users": [{
                                "id": uuid,
                                "encryption": "none"
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "tls"
                    }
                })
        elif line.startswith("trojan://"):
            match = re.match(r'trojan://([^@]+)@([^:]+):(\d+)', line)
            if match:
                password, host, port = match.groups()
                outbounds.append({
                    "tag": tag,
                    "protocol": "trojan",
                    "settings": {
                        "servers": [{
                            "address": host,
                            "port": int(port),
                            "password": password
                        }]
                    },
                    "streamSettings": {
                        "security": "tls"
                    }
                })
        elif line.startswith("ss://"):
            try:
                ss = line[5:]
                if "@" in ss:
                    method_pass, server = ss.split("@")
                    method, password = base64.b64decode(method_pass + '==').decode().split(":")
                    host, port = server.split(":")
                else:
                    decoded = base64.b64decode(ss + '==').decode()
                    method, password, host, port = re.match(r'([^:]+):([^@]+)@([^:]+):(\d+)', decoded).groups()
                outbounds.append({
                    "tag": tag,
                    "protocol": "shadowsocks",
                    "settings": {
                        "servers": [{
                            "address": host,
                            "port": int(port),
                            "method": method,
                            "password": password
                        }]
                    }
                })
            except:
                continue
    config = {
        "outbounds": outbounds
    }
    with open("xray_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def run_xray_test():
    try:
        result = subprocess.run([
            "xray", "test", "-c", "xray_config.json",
            "--test.url", "https://www.google.com/generate_204",
            "--test.timeout", "5s", "--test.parallel", "10"
        ], capture_output=True, text=True)
        print("Xray stdout:", result.stdout)
        print("Xray stderr:", result.stderr)
        return json.loads(result.stdout)
    except Exception as e:
        print("❌ Xray test failed:", e)
        return []

def main():
    with open("v2_raw.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    build_xray_config(lines)
    results = run_xray_test()

    enriched = []
    for i, line in enumerate(lines):
        tag = f"node{i}"
        delay = next((r["delay"] for r in results if r["tag"] == tag), float("inf"))
        ip, _ = extract_ip_port(line)
        city = get_city_cn(ip) if ip else "未知"
        enriched.append((city, delay, line))

    top = sorted(enriched, key=lambda x: x[1])[:20]

    with open("v2.txt", "w", encoding="utf-8") as f:
        for i, (city, delay, line) in enumerate(top, 1):
            f.write(format_config(line, i, city) + "\n")

if __name__ == "__main__":
    main()
