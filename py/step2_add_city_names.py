import os
import base64
import json
import requests
import urllib.parse
import zipfile
import ip2location

# 数据库下载地址和文件名
DB_URL = "https://download.ip2location.com/lite/IP2LOCATION-LITE-DB3.IPV4.BIN.ZIP"
DB_ZIP = "IP2LOCATION-LITE-DB3.IPV4.BIN.ZIP"
DB_BIN = "IP2LOCATION-LITE-DB3.IPV4.BIN"
V2_PATH = os.path.join(os.getcwd(), "v2.txt")

def download_ip2location_db():
    if os.path.exists(DB_BIN):
        print("✅ IP2Location 数据库已存在，跳过下载")
        return
    print("⬇️ 正在下载 IP2Location 城市数据库...")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(DB_URL, headers=headers, timeout=10)
    with open(DB_ZIP, "wb") as f:
        f.write(r.content)
    if not zipfile.is_zipfile(DB_ZIP):
        raise Exception("❌ 下载的文件不是有效的 ZIP 格式")
    with zipfile.ZipFile(DB_ZIP, 'r') as zip_ref:
        zip_ref.extractall(".")
    os.remove(DB_ZIP)
    print("✅ 数据库下载并解压完成")

def get_city(ip, db):
    try:
        rec = db.get_all(ip)
        return rec.city or "未知"
    except:
        return "未知"

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
    download_ip2location_db()
    db = ip2location.IP2Location(DB_BIN)

    if not os.path.exists(V2_PATH):
        print("❌ 未找到 v2.txt 文件")
        return

    with open(V2_PATH, 'r', encoding='utf-8') as f:
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
            print(f"⚠️ 跳过不支持的格式: {line}")
            continue

        city = get_city(ip, db) if ip else "未知"
        new_line = update_node_name(line, idx, city, obj)
        new_lines.append(new_line)

    with open(V2_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("✅ 节点名称已更新为 序号-城市（使用本地数据库）")

if __name__ == "__main__":
    main()
