import yaml

def parse_v2ray_line(line):
    return {
        'name': line,
        'type': 'vmess',
        'server': 'example.com',
        'port': 443,
        'uuid': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        'alterId': 0,
        'cipher': 'auto'
    }

with open('v2.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

proxies = [parse_v2ray_line(line) for line in lines]

config = {
    'port': 7890,
    'socks-port': 7891,
    'allow-lan': True,
    'mode': 'Rule',
    'proxies': proxies,
    'proxy-groups': [],
    'rules': ['DOMAIN-SUFFIX,google.com,DIRECT']
}

with open('config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True)
