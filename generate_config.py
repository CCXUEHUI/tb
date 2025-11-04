import base64
import json
import yaml

def parse_vmess(line):
    raw = line[8:]
    data = json.loads(base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8"))
    return {
        "name": data.get("ps", "Unnamed"),
        "type": "vmess",
        "server": data["add"],
        "port": int(data["port"]),
        "uuid": data["id"],
        "alterId": int(data.get("aid", 0)),
        "cipher": data.get("scy", "auto"),
        "tls": data.get("tls", "") == "tls",
        "network": data.get("net", "tcp"),
        "ws-opts": {
            "path": data.get("path", ""),
            "headers": {"Host": data.get("host", "")}
        } if data.get("net") == "ws" else None
    }

def parse_other(line):
    if line.startswith("vless://") or line.startswith("trojan://"):
        return {
            "name": line.split("#")[-1] if "#" in line else "Unnamed",
            "type": "trojan" if line.startswith("trojan://") else "vless",
            "server": "example.com",  # 可解析 hostname
            "port": 443,
            "uuid": "fake-uuid",
            "tls": True
        }

def main():
    proxies = []
    with open("v2.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("vmess://"):
                proxies.append(parse_vmess(line))
            elif line.startswith("vless://") or line.startswith("trojan://"):
                proxies.append(parse_other(line))

    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "Auto",
                "type": "url-test",
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300,
                "proxies": [p["name"] for p in proxies]
            }
        ],
        "rules": [
            "DOMAIN-SUFFIX,google.com,Auto",
            "DOMAIN-SUFFIX,youtube.com,Auto",
            "DOMAIN-SUFFIX,facebook.com,Auto",
            "GEOIP,CN,DIRECT",
            "MATCH,Auto"
        ]
    }

    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    print(f"✅ 生成 config.yaml，包含 {len(proxies)} 个节点")

if __name__ == "__main__":
    main()
