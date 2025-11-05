import os
import platform
import requests
import subprocess
import time
import yaml
import gzip
import shutil

CONFIG_PATH = "config.yaml"
CLASH_API = "http://127.0.0.1:9090"
PROXY_PORT = 7890
MIHOMO_BIN = "mihomo"

def get_mihomo_url():
    arch = platform.machine().lower()
    if arch in ['x86_64', 'amd64']:
        return "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.15/mihomo-linux-amd64-v1.19.15.gz"
    elif arch in ['arm64', 'aarch64']:
        return "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.15/mihomo-linux-arm64-v1.19.15.gz"
    else:
        raise Exception(f"不支持的架构: {arch}")

def download_and_prepare_mihomo():
    if os.path.exists(MIHOMO_BIN):
        print("已存在 mihomo 可执行文件，跳过下载")
        return
    url = get_mihomo_url()
    print(f"下载 mihomo: {url}")
    r = requests.get(url, stream=True)
    with open("mihomo.gz", "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("解压 mihomo.gz...")
    with gzip.open("mihomo.gz", "rb") as f_in:
        with open(MIHOMO_BIN, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.chmod(MIHOMO_BIN, 0o755)
    print("mihomo 准备完成")

def run_mihomo():
    print("启动 mihomo...")
    return subprocess.Popen([f"./{MIHOMO_BIN}", "-f", CONFIG_PATH])

def stop_mihomo(process):
    if process:
        process.terminate()
        print("mihomo 已关闭")

def wait_for_api(timeout=10):
    for _ in range(timeout):
        try:
            r = requests.get(f"{CLASH_API}/configs")
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    raise Exception("mihomo API 启动失败")

def switch_proxy(group, proxy_name):
    url = f"{CLASH_API}/proxies/{group}"
    requests.put(url, json={"name": proxy_name})

def test_google_latency():
    try:
        start = time.time()
        r = requests.get("https://www.google.com/generate_204", proxies={
            "http": f"http://127.0.0.1:{PROXY_PORT}",
            "https": f"http://127.0.0.1:{PROXY_PORT}"
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
    download_and_prepare_mihomo()
    process = run_mihomo()
    try:
        wait_for_api()
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
        stop_mihomo(process)

if __name__ == "__main__":
    main()
