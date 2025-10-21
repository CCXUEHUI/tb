import json
import base64
import urllib.parse
import requests
import subprocess
import os

def parse_nodes():
    with open("v2_raw.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    nodes = []
    for line in lines:
        if line.startswith("vmess://"):
            try:
                raw = base64.b64decode(line[8:] + '==').decode("utf-8")
                data = json.loads(raw)
                nodes.append({"type": "vmess", "config": data, "raw": line})
            except:
                continue
        elif line.startswith("vless://") or line.startswith("trojan://") or line.startswith("ss://"):
            nodes.append({"type": "url", "raw": line})
    return nodes

def build_singbox_config(nodes):
    outbounds = []
    for i, node in enumerate(nodes):
        tag = f"node{i}"
        if node["type"] == "vmess":
            cfg = node["config"]
            outbounds.append({
                "type": "vmess",
                "tag": tag,
                "server": cfg["add"],
                "server_port": int(cfg["port"]),
                "uuid": cfg["id"],
                "alter_id": int(cfg.get("aid", 0)),
                "security": cfg.get("scy", "auto"),
                "transport": {
                    "type": cfg.get("net", "tcp"),
                    "path": cfg.get("path", ""),
                    "host": cfg.get("host", ""),
                    "tls": cfg.get("tls", "") == "tls"
                }
            })
        else:
            outbounds.append({
                "type": "selector",
                "tag": tag,
                "outbounds": [node["raw"]]  # placeholder
            })
    config = {
        "outbounds": outbounds
    }
    with open("singbox_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def run_singbox_test():
    result = subprocess.run(["sing-box", "test", "-c", "singbox_config.json", "--test.url", "https://www.google.com/generate_204", "--test.timeout", "5s", "--test.parallel", "10"], capture_output=True, text=True)
    return json.loads(result.stdout)

def get_city(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=city&lang=zh-CN", timeout=5)
        if r.status_code == 200:
            return r.json().get("city", "未知")
    except:
        pass
    return "未知"

def format_node(raw, index, city):
    label = f"{str(index).zfill(2)}-{city}"
    if raw.startswith("vmess://"):
        try:
            data = json.loads(base64.b64decode(raw[8:] + '==').decode("utf-8"))
            data["ps"] = label
            new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            return "vmess://" + base64.b64encode(new_json.encode("utf-8")).decode("utf-8")
        except:
            return raw
    else:
        base = raw.split("#")[0]
        return f"{base}#{urllib.parse.quote(label)}"

def main():
    nodes = parse_nodes()
    build_singbox_config(nodes)
    results = run_singbox_test()

    enriched = []
    for i, node in enumerate(nodes):
        tag = f"node{i}"
        delay = next((r["delay"] for r in results if r["tag"] == tag), float("inf"))
        ip = node["config"]["add"] if node["type"] == "vmess" else None
        city = get_city(ip) if ip else "未知"
        enriched.append((city, delay, node["raw"]))

    # 按城市名拼音排序，选前20个
    top = sorted(enriched, key=lambda x: x[0])[:20]

    with open("v2.txt", "w", encoding="utf-8") as f:
        for i, (city, delay, raw) in enumerate(top, 1):
            f.write(format_node(raw, i, city) + "\n")

if __name__ == "__main__":
    main()
