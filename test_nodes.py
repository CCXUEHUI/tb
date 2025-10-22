import json
import base64
import re
import subprocess

# 构建 Xray 配置文件
def build_xray_config(nodes):
    outbounds = []
    for i, line in enumerate(nodes):
        tag = f"node{i}"
        if line.startswith("vmess://"):
            try:
                raw = line[8:]
                padded = raw + '=' * (-len(raw) % 4)
                data = json.loads(base64.b64decode(padded).decode("utf-8"))
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
    config = {
        "outbounds": outbounds
    }
    with open("xray_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 执行 Xray 测速命令
def run_xray_test():
    try:
        result = subprocess.run([
            "xray", "test", "-c", "xray_config.json",
            "--test.url", "http://www.gstatic.com/generate_204",
            "--test.timeout", "5s", "--test.parallel", "10"
        ], capture_output=True, text=True)

        if result.returncode != 0 or not result.stdout.strip():
            print("❌ Xray 测速失败")
            return []

        return json.loads(result.stdout)
    except Exception as e:
        print("❌ 执行异常:", e)
        return []

# 主流程
def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    build_xray_config(lines)
    results = run_xray_test()

    # 提取延迟低于 600ms 的节点
    valid_tags = {r["tag"] for r in results if r.get("delay", 9999) < 600}
    filtered = [line for i, line in enumerate(lines) if f"node{i}" in valid_tags]

    print(f"✅ 保留 {len(filtered)} 个延迟 < 600ms 的节点")

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(filtered))

if __name__ == "__main__":
    main()
