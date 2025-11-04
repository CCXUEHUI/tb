import yaml
import subprocess

def test_latency(proxy):
    name = proxy['name']
    server = proxy['server']
    try:
        g_ping = subprocess.check_output(['ping', '-c', '2', 'google.com'], timeout=5).decode()
        y_ping = subprocess.check_output(['ping', '-c', '2', 'youtube.com'], timeout=5).decode()
        avg = (extract_avg(g_ping) + extract_avg(y_ping)) / 2
        return avg
    except:
        return 9999

def extract_avg(ping_output):
    for line in ping_output.splitlines():
        if 'avg' in line or 'rtt' in line:
            parts = line.split('/')
            return float(parts[4])
    return 9999

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

for proxy in config['proxies']:
    latency = test_latency(proxy)
    if latency < 400:
        proxy['name'] = f"{proxy['name']}-{int(latency)}ms"

with open('config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True)
