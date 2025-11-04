import yaml

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

with open('v2.txt', 'w', encoding='utf-8') as f:
    for proxy in config['proxies']:
        line = f"{proxy['name']}|{proxy['server']}:{proxy['port']}"
        f.write(line + '\n')
