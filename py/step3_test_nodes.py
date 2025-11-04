import os
import platform
import requests
import zipfile
import subprocess
import time
import yaml

CLASH_API = "http://127.0.0.1:9090"
CONFIG_PATH = "config.yaml"
CLASH_DIR = "clash_meta"
CLASH_BIN = os.path.join(CLASH_DIR, "clash.meta.exe" if platform.system().lower() == "windows" else "clash.meta")

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
    api_url = "https://api.github.com/repos/MetaCubeX/Clash.Meta/releases/latest"
    resp = requests.get(api_url)
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
            os.chmod(CLASH_BIN, 0o755)
            return
    raise Exception("未找到匹配的 Clash.Meta 版本")

def run_clash():
    print("启动 Clash...")
    return subprocess.Popen([CLASH_BIN, "-f", CONFIG_PATH])

def stop_clash(process):
    if process:
        process.terminate()
        print("Clash 已关闭")

def wait_for_clash_api(timeout=10):
    for _ in range(timeout):
        try:
            r = requests.get(f"{CLASH_API}/configs")
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    raise Exception("Clash API 启动失败")

def switch_proxy(group, proxy_name):
    url = f"{CLASH_API}/proxies/{group}"
    requests.put(url, json={"name": proxy_name})

def test_google_latency():
    try:
        start = time.time()
        r = requests.get("https://www.google.com/generate_204", proxies={
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        }, timeout=5)
        return int((time.time() - start) * 1000)
    except:
        return 9999

def update_config_names(latency_map):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    for proxy in config.get('proxies', []):
        name = proxy['name']
        if name in latency_map:
            proxy['name'] = f"{name}-{latency_map[name]}ms"
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

def main():
    if not os.path.exists(CLASH_BIN):
        download_clash_meta()
    clash_process = run_clash()
    try:
        wait_for_clash_api()
        proxies = requests.get(f"{CLASH_API}/proxies").json()
        groups = [k for k, v in proxies.items() if v['type'] == 'Selector']
        if not groups:
            raise Exception("未找到 proxy-groups")
        group = groups[0]
        all_proxies = proxies[group]['all']
        latency_map = {}
        for name in all_proxies:
            print(f"切换节点: {name}")
            switch_proxy(group, name)
            time.sleep(2)
            latency = test_google_latency()
            print(f"→ {name}: {latency}ms")
            latency_map[name] = latency
        update_config_names(latency_map)
    finally:
        stop_clash(clash_process)

if __name__ == "__main__":
    main()
