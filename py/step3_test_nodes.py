import os
import platform
import requests
import subprocess
import time
import shutil
import json
import base64

V2RAY_URL_AMD64 = "https://github.com/v2fly/v2ray-core/releases/latest/download/v2ray-linux-64.zip"
V2RAY_URL_ARM64 = "https://github.com/v2fly/v2ray-core/releases/latest/download/v2ray-linux-arm64.zip"
V2RAY_DIR = "v2ray"
V2RAY_BIN = os.path.join(V2RAY_DIR, "v2ray")
V2RAY_CONFIG = os.path.join(V2RAY_DIR, "config.json")
V2_TXT = "v2.txt"
LOCAL_SOCKS_PORT = 1080

def detect_arch():
    arch = platform.machine().lower()
    if arch in ['x86_64', 'amd64']:
        return V2RAY_URL_AMD64
    elif arch in ['arm64', 'aarch64']:
        return V2RAY_URL_ARM64
    else:
        raise Exception(f"Unsupported architecture: {arch}")

def download_v2ray():
    if os.path.exists(V2RAY_BIN):
        print("V2Ray 已存在，跳过下载")
        return
    url = detect_arch()
    print(f"下载 V2Ray: {url}")
    zip_path = "v2ray.zip"
    with open(zip_path, "wb") as f:
        f.write(requests.get(url).content)
    shutil.unpack_archive(zip_path, V2RAY_DIR)
    os.chmod(V2RAY_BIN, 0o755)
    print("V2Ray 准备完成")

def parse_node(line):
    if line.startswith("vmess://"):
        decoded = base64.b64decode(line[8:]).decode()
        obj = json.loads(decoded)
        return {
            "protocol": "vmess",
            "tag": obj.get("ps", "vmess"),
            "settings": {
                "vnext": [{
                    "address": obj["add"],
                    "port": int(obj["port"]),
                    "users": [{
                        "id": obj["id"],
                        "alterId": int(obj.get("aid", 0)),
                        "security": obj.get("scy", "auto")
                    }]
                }]
            },
            "streamSettings": {
                "network": obj.get("net", "tcp"),
                "security": obj.get("tls", "")
            }
        }
    # 可扩展支持 vless/ss/trojan
    return None

def generate_config(outbound):
    config = {
        "inbounds": [{
            "port": LOCAL_SOCKS_PORT,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": False}
        }],
        "outbounds": [outbound]
    }
    with open(V2RAY_CONFIG, "w") as f:
        json.dump(config, f, indent=2)

def run_v2ray():
    return subprocess.Popen([V2RAY_BIN, "-config", V2RAY_CONFIG])

def stop_v2ray(process):
    if process:
        process.terminate()
        time.sleep(1)

def test_google_latency():
    proxies = {
        "http": f"socks5h://127.0.0.1:{LOCAL_SOCKS_PORT}",
        "https": f"socks5h://127.0.0.1:{LOCAL_SOCKS_PORT}"
    }
    try:
        start = time.time()
        r = requests.get("https://www.google.com/generate_204", proxies=proxies, timeout=5)
        return int((time.time() - start) * 1000)
    except:
        return 9999

def main():
    download_v2ray()
    with open(V2_TXT, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    results = []
    for line in lines:
        node = parse_node(line)
        if not node:
            print("跳过不支持的节点格式")
            continue
        print(f"测试节点: {node['tag']}")
        generate_config(node)
        proc = run_v2ray()
        time.sleep(2)
        latency = test_google_latency()
        print(f"→ {node['tag']}: {latency}ms")
        stop_v2ray(proc)
        results.append((line, node['tag'], latency))
    # 排序并写回
    sorted_results = sorted(results, key=lambda x: x[2])
    with open(V2_TXT, "w") as f:
        for raw, name, latency in sorted_results:
            f.write(f"{name}-{latency}ms\n")
    print("测速完成，已更新 v2.txt")

if __name__ == "__main__":
    main()
