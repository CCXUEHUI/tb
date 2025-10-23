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
            except Exception as e:
                print(f"⚠️ vmess 节点解析失败: {e}")
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
    print(f"✅ 已生成配置，共 {len(outbounds)} 个节点")

def run_singbox_test():
    try:
        result = subprocess.run([
            "sing-box", "test", "-c", "singbox_config.json", "--target", "latency"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ sing-box 测速失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return []

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print("❌ sing-box 输出不是有效的 JSON")
            print("原始输出:", result.stdout)
            return []

    except FileNotFoundError:
        print("❌ 未找到 sing-box，请确认是否正确安装并添加到系统路径")
        return []
    except Exception as e:
        print("❌ 执行异常:", e)
        return []

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not lines:
        print("⚠️ v2.txt 中没有有效节点，跳过测速")
        return

    build_singbox_config(lines)

    with open("singbox_config.json", "r", encoding="utf-8") as f:
        print("📄 sing-box 配置内容:")
        print(f.read())

    results = run_singbox_test()
    valid_tags = {r["tag"] for r in results if r.get("latency", 9999) < 600}
    filtered = [line for i, line in enumerate(lines) if f"node{i}" in valid_tags]

    print(f"✅ 保留 {len(filtered)} 个延迟 < 600ms 的节点")

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(filtered) + "\n")

if __name__ == "__main__":
    main()
