import json
import base64
import re
import subprocess

# 解析节点并构建 Xray 配置
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

# 调用 Xray 进行测速
def run_xray_test():
    try:
        result = subprocess.run([
            "xray", "test", "-c", "xray_config.json",
            "--test.url", "https://www.google.com/generate_204",
            "--test.timeout", "5s", "--test.parallel", "10"
        ], capture_output=True, text=True)

        print("📤 Xray stdout:\n", result.stdout)
        print("📥 Xray stderr:\n", result.stderr)

        if "unknown command" in result.stderr or not result.stdout.strip():
            print("❌ Xray test 命令失败或无输出，请检查版本或配置")
            return []

        return json.loads(result.stdout)
    except Exception as e:
        print("❌ Xray test 异常:", e)
        return []

# 主流程
def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    build_xray_config(lines)
    results = run_xray_test()

    for r in results:
        print(f"{r['tag']}: {r['delay']}ms")

if __name__ == "__main__":
    main()
