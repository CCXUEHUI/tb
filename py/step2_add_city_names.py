import os
import base64
import json
import requests
import urllib.parse

V2_PATH = os.path.join(os.getcwd(), "v2.txt")

def get_city(ip):
    try:
        r = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        data = r.json()
        city_en = data.get('city', '')
        return translate_city(city_en) if city_en else "未知"
    except:
        return "未知"

def translate_city(city_en):
    try:
        url = f"https://translate.appworlds.cn?text={urllib.parse.quote(city_en)}&from=en&to=zh-CN"
        r = requests.get(url, timeout=5)
        data = r.json()
        return data.get("data", city_en)
    except:
        return city_en

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
        return url.hostname, url
    except:
        return "", None

def parse_ip_from_trojan(line):
    try:
        url = urllib.parse.urlparse(line)
        return url.hostname, url
    except:
        return "", None

def parse_ip_from_ss(line):
    try:
        raw = line[5:]
        if '@' in raw:
            parts = raw.split('@')
            host_port = parts[1]
            ip = host_port.split(':')[0]
            return ip, None
        else:
            padded = raw + '=' * (-len(raw) % 4)
            decoded = base64.b64decode(padded).decode()
            if '@' in decoded:
                ip = decoded.split('@')[1].split(':')[0]
                return ip, None
        return "", None
    except:
        return "", None

def update_node_name(line, index, city, obj=None, url_obj=None):
    name = f"{index}-{city}"
    if line.startswith("vmess://") and obj:
        obj['ps'] = name
        new_encoded = base64.b64encode(json.dumps(obj, ensure_ascii=False).encode()).decode().replace('=', '')
        return f"vmess://{new_encoded}"
    elif line.startswith("vless://") or line.startswith("trojan://"):
        query = urllib.parse.parse_qs(url_obj.query)
        query['remarks'] = [name]
        new_query = urllib.parse.urlencode(query, doseq=True)
        new_url = url_obj._replace(query=new_query)
        return urllib.parse.urlunparse(new_url)
    elif line.startswith("ss://"):
        return f"{line}#{name}"
    else:
        return line

def main():
    if not os.path.exists(V2_PATH):
        print("❌ 未找到 v2.txt 文件")
        return

    with open(V2_PATH, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    new_lines = []
    for idx, line in enumerate(lines, start=1):
        ip, obj = "", None
        url_obj = None
        if line.startswith("vmess://"):
            ip, obj = parse_ip_from_vmess(line)
        elif line.startswith("vless://"):
            ip, url_obj = parse_ip_from_vless(line)
        elif line.startswith("trojan://"):
            ip, url_obj = parse_ip_from_trojan(line)
        elif line.startswith("ss://"):
            ip, obj = parse_ip_from_ss(line)
        else:
            print(f"⚠️ 跳过不支持的格式: {line}")
            continue

        city = get_city(ip) if ip else "未知"
        new_line = update_node_name(line, idx, city, obj, url_obj)
        new_lines.append(new_line)

    with open(V2_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("✅ 节点名称已更新为：序号-城市中文名")

if __name__ == "__main__":
    main()
