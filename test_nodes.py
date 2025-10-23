import json
import base64
import re
import subprocess

def build_singbox_config(nodes):
    outbounds = []
    for i, line in enumerate(nodes):
        tag = f"node{i}"
        if line.startswith("vmess://"):
            try:
                raw = line[8:]
                padded = raw + '=' * (-len(raw) % 4)
                data = json.loads(base64.b64decode(padded).decode("utf-8"))
                outbounds.append({
                    "type": "vmess",
                    "tag": tag,
                    "server": data["add"],
                    "server_port": int(data["port"]),
                    "uuid": data["id"],
                    "alter_id": int(data.get("aid", 0)),
                    "security": data.get("scy", "auto"),
                    "transport": {
                        "type": data.get("net", "tcp"),
                        "path": data.get("path", ""),
                        "headers": {
                            "Host": data.get("host", "")
                        }
                    },
                    "tls": {
                        "enabled": data.get("tls") == "tls"
                    }
                })
            except:
                continue
        elif line.startswith("vless://"):
            match = re.match(r'vless://([^@]+)@([^:]+):(\d+)', line)
            if match:
                uuid, host, port = match.groups()
                outbounds.append({
                    "type": "vless",
                    "tag": tag,
                    "server": host,
                    "server_port": int(port),
                    "uuid": uuid,
                    "flow": "",
                    "tls": {
                        "enabled": True
                    }
                })
        elif line.startswith("trojan://"):
            match = re.match(r'trojan://([^@]+)@([^:]+):(\d+)', line)
            if match:
                password, host, port = match.groups()
                outbounds.append({
                    "type": "trojan",
                    "tag": tag,
                    "server": host,
                    "server_port": int(port),
                    "password": password,
                    "tls": {
                        "enabled": True
                    }
                })
    config = {
        "outbounds": outbounds
    }
    with open("singbox_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def run_singbox_test():
    try:
        result = subprocess.run([
            "sing-box", "test", "-c", "singbox_config.json", "--target", "latency"
        ], capture_output=True, text=True)

        if result.returncode != 0 or not result.stdout.strip():
            print("❌ sing-box 测速失败")
            return []

        return json.loads(result.stdout)
    except Exception as e:
        print("❌ 执行异常:", e)
        return []

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    build_singbox_config(lines)
    results = run_singbox_test()

    valid_tags = {r["tag"] for r in results if r.get("latency", 9999) < 600}
    filtered = [line for i, line in enumerate(lines) if f"node{i}" in valid_tags]

    print(f"✅ 保留 {len(filtered)} 个延迟 < 600ms 的节点")

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(filtered))

if __name__ == "__main__":
    main()
