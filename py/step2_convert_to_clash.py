import yaml
import base64
import json

def parse_vmess(line):
    if not line.startswith('vmess://'):
        return None
    try:
        decoded = base64.b64decode(line[8:] + '=' * (-len(line[8:]) % 4)).decode()
        data = json.loads(decoded)
        proxy = {
            'name': data.get('ps', '未命名节点'),
            'type': 'vmess',
            'server': data.get('add'),
            'port': int(data.get('port')),
            'uuid': data.get('id'),
            'alterId': int(data.get('aid', 0)),
            'cipher': 'auto',
            'tls': 'tls' if data.get('tls', '') == 'tls' else False,
            'network': data.get('net', 'ws'),
        }
        # 添加 ws-opts（如果是 ws 网络）
        if proxy['network'] == 'ws':
            proxy['ws-opts'] = {
                'path': data.get('path', ''),
                'headers': {
                    'Host': data.get('host', '')
                }
            }
        return proxy
    except Exception as e:
        print(f"解析失败: {line[:30]}... - {e}")
        return None

# 读取 v2.txt
with open('v2.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

# 转换为 Clash 节点
proxies = [parse_vmess(line) for line in lines if parse_vmess(line)]

# 构造 Clash 配置
config = {
    'port': 7890,
    'socks-port': 7891,
    'allow-lan': True,
    'mode': 'Rule',
    'proxies': proxies,
    'proxy-groups': [],
    'rules': ['DOMAIN-SUFFIX,google.com,DIRECT']
}

# 写入 config.yaml
with open('config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
