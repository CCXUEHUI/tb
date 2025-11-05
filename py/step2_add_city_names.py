import os
import base64
import json
import requests
import urllib.parse

def get_city(ip):
    try:
        r = requests.get(f'https://ipapi.co/{ip}/city/', timeout=5)
        return r.text.strip()
    except:
        return '未知'

def parse_ip_from_vmess(line):
    try:
        raw = line[8:]
        padded = raw + '=' * (-len(raw) % 4)
        decoded = base64.b64decode(padded).decode()
        obj = json.loads(decoded)
        return obj.get("add", ""), obj
    except:
        return "", None

def parse_ip_from_vless(line):
    try:
        url = urllib.parse.urlparse(line)
        return url.hostname, None
    except:
        return "", None

def parse_ip_from_trojan(line):
    try:
        url = urllib.parse.urlparse(line)
        return url.hostname, None
    except:
        return "", None

def parse_ip_from_ss(line):
    try:
        raw = line[5:]
        if '@' in raw:
            # ss://method:password@host:port
            parts = raw.split('@')
            host_port = parts[1]
            ip = host_port.split(':')[0]
            return ip, None
        else:
            # ss://base64_encoded
            padded = raw + '=' * (-len(raw) % 4)
            decoded = base64.b64decode(padded).decode()
            if '@' in decoded:
                ip = decoded.split('@')[1].split(':')[0]
                return ip, None
        return "", None
    except:
        return "", None

def update_node_name(line, index, city, obj=None):
    if line.startswith("vmess://") and obj:
        obj['ps'] = f"{index}-{city}"
        new_encoded = base64.b64encode(json.dumps(obj, ensure_ascii=False).encode()).decode().replace('=', '')
        return f"vmess://{new_encoded}"
    elif line.startswith("vless://") or line.startswith("trojan://") or line.startswith("ss://"):
        return f"{index}-{city}|{line}"
    else:
        return line

def main():
    input_path = os.path.join(os.getcwd(), "v2.txt")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    new_lines = []
    for idx, line in enumerate(lines, start=1):
        ip, obj = "", None
        if line.startswith("vmess://"):
            ip, obj = parse_ip_from_vmess(line)
        elif line.startswith("vless://"):
            ip, obj = parse_ip_from_vless(line)
        elif line.startswith("trojan://"):
            ip, obj = parse_ip_from_trojan(line)
        elif line.startswith("ss://"):
            ip, obj = parse_ip_from_ss(line)
        else:
            print(f"跳过不支持的格式: {line}")
            continue

        city = get_city(ip) if ip else "未知"
        new_line = update_node_name(line, idx, city, obj)
        new_lines.append(new_line)

    with open(input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("节点名称已更新为 序号-城市 格式")

if __name__ == "__main__":
    main()
