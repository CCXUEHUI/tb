import os
import platform
import requests
import zipfile
import subprocess
import time
import yaml

CLASH_API = "https://api.github.com/repos/MetaCubeX/Clash.Meta/releases/latest"
CLASH_DIR = "clash_meta"
CONFIG_PATH = "config.yaml"
LOCAL_PROXY_PORT = 7890
TEST_URLS = [
    "https://www.google.com/generate_204",
    "https://www.youtube.com"
]

def get_system_arch():
    sys = platform.system().lower()
    arch = platform.machine().lower()
    if 'windows' in sys:
        sys = 'windows'
    elif 'darwin' in sys:
        sys = 'darwin'
    elif 'linux' in sys:
        sys = 'linux'
    else:
        raise Exception("Unsupported OS")

    if arch in ['x86_64', 'amd64']:
        arch = 'amd64'
    elif arch in ['arm64', 'aarch64']:
        arch = 'arm64'
    else:
        raise Exception("Unsupported architecture")

    return sys, arch

def download_clash_meta():
    sys, arch = get_system_arch()
    print(f"检测系统: {sys}, 架构: {arch}")
    resp = requests.get(CLASH_API)
    assets = resp.json().get("assets", [])
    for asset in assets:
        name = asset["name"]
        if sys in name and arch in name and name.endswith(".zip"):
            url = asset["browser_download_url"]
            print(f"下载 Clash.Meta: {name}")
            clash_zip = "clash_meta.zip"
            with open(clash_zip, "wb") as f:
                f.write(requests.get(url).content)
            with zipfile.ZipFile(clash_zip, 'r') as zip_ref:
                zip_ref.extractall(CLASH_DIR)
            clash_path = os.path.join(CLASH_DIR, "clash.meta.exe" if sys == "windows" else "clash.meta")
            os.chmod(clash_path, 0o755)
            return clash_path
    raise Exception("未找到匹配的 Clash.Meta 版本")

def run_clash(clash_path, config_path="config.yaml"):
    print("启动 Clash...")
    process = subprocess.Popen([clash_path, "-f", config_path])
    time.sleep(5)  # 等待 Clash 启动
    return process

def stop_clash(process):
    if process:
        process.terminate()
        print("Clash 已关闭")

def test_latency_via_proxy(proxy_port, timeout=3):
    proxies = {
        'http': f'http://127.0.0.1:{proxy_port}',
        'https': f'http://127.0.0.1:{proxy_port}'
    }
    latencies = []
    for url in TEST_URLS:
        try:
            start = time.time()
            r = requests.get(url, proxies=proxies, timeout=timeout)
            latency = int((time.time() - start) * 1000)
            latencies.append(latency)
        except:
            latencies.append(9999)
    return sum(latencies) // len(latencies)

def update_config_with_latency():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    for proxy in config.get('proxies', []):
        print(f"测试节点: {proxy.get('name')}")
        latency = test_latency_via_proxy(LOCAL_PROXY_PORT)
        old_name = proxy.get('name', 'Unnamed')
        proxy['name'] = f"{old_name}-{latency}ms"

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

# 主流程
if not os.path.exists(CLASH_DIR):
    clash_exec = download_clash_meta()
else:
    clash_exec = os.path.join(CLASH_DIR, "clash.meta.exe" if platform.system().lower() == "windows" else "clash.meta")

clash_process = run_clash(clash_exec)
try:
    update_config_with_latency()
finally:
    stop_clash(clash_process)
