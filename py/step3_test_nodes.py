import yaml
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_avg(ping_output):
    for line in ping_output.splitlines():
        if 'avg' in line or 'rtt' in line:
            parts = line.split('/')
            try:
                return float(parts[4])
            except:
                continue
    return 9999

def test_latency(proxy):
    name = proxy['name']
    server = proxy['server']
    try:
        g_ping = subprocess.check_output(['ping', '-c', '1', '-W', '1', 'google.com'], timeout=3).decode()
        y_ping = subprocess.check_output(['ping', '-c', '1', '-W', '1', 'youtube.com'], timeout=3).decode()
        avg = (extract_avg(g_ping) + extract_avg(y_ping)) / 2
        return name, avg
    except Exception as e:
        return name, 9999

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

proxies = config.get('proxies', [])
updated_proxies = []

# 并发测试所有节点
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_proxy = {executor.submit(test_latency, proxy): proxy for proxy in proxies}
    for future in as_completed(future_to_proxy):
        proxy = future_to_proxy[future]
        name, latency = future.result()
        if latency < 400:
            proxy['name'] = f"{name}-{int(latency)}ms"
        updated_proxies.append(proxy)

# 更新配置文件
config['proxies'] = updated_proxies
with open('config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True)
