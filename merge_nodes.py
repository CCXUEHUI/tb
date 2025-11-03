# merge_nodes.py
# ✅ 清除原有节点名称，统一重命名为：序号-城市中文名-延迟ms

import re
import base64
import json
from urllib.parse import urlparse, urlunparse

# 城市关键词映射（可扩展）
city_map = {
    "tokyo": "东京", "japan": "日本", "osaka": "大阪",
    "hongkong": "香港", "hk": "香港",
    "taiwan": "台湾", "taipei": "台北",
    "singapore": "新加坡", "sg": "新加坡",
    "seoul": "首尔", "korea": "韩国",
    "london": "伦敦", "uk": "英国",
    "frankfurt": "法兰克福", "germany": "德国",
    "paris": "巴黎", "france": "法国",
    "new york": "纽约", "los angeles": "洛杉矶",
    "us": "美国", "usa": "美国",
    "canada": "加拿大", "toronto": "多伦多",
    "sydney": "悉尼", "australia": "澳大利亚"
}

def extract_city(text):
    text = text.lower()
    for key, name in city_map.items():
        if key in text:
            return name
    return "未知"

def extract_latency(text):
    match = re.search(r'#latency=(\d+)', text)
    return int(match.group(1)) if match else None

def clean_and_rename(line, index):
    latency = extract_latency(line)
    city = extract_city(line)

    if line.startswith("vmess://"):
        try:
            raw = line[8:]
            decoded = base64.b64decode(raw + '=' * (-len(raw) % 4)).decode("utf-8")
            data = json.loads(decoded)
            data["ps"] = f"{index}-{city}-{latency}ms"
            new_raw = base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode().rstrip("=")
            return f"vmess://{new_raw}"
        except:
            return line  # fallback
    elif line.startswith("vless://") or line.startswith("trojan://"):
        try:
            url = line.split("#")[0]  # remove fragment
            return f"{url}#{index}-{city}-{latency}ms"
        except:
            return line
    else:
        return line

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    renamed = []
    count = 1
    for line in lines:
        if extract_latency(line) is not None:
            renamed.append(clean_and_rename(line, count))
            count += 1
        else:
            renamed.append(line)

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed) + "\n")

if __name__ == "__main__":
    main()
