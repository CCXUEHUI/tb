# merge_nodes.py
# ✅ 节点重命名：序号-城市中文名-延迟ms

import re

# 城市关键词映射（可扩展）
city_map = {
    "tokyo": "东京",
    "japan": "日本",
    "osaka": "大阪",
    "hongkong": "香港",
    "hk": "香港",
    "taiwan": "台湾",
    "taipei": "台北",
    "singapore": "新加坡",
    "sg": "新加坡",
    "seoul": "首尔",
    "korea": "韩国",
    "london": "伦敦",
    "uk": "英国",
    "frankfurt": "法兰克福",
    "germany": "德国",
    "paris": "巴黎",
    "france": "法国",
    "new york": "纽约",
    "los angeles": "洛杉矶",
    "us": "美国",
    "usa": "美国",
    "canada": "加拿大",
    "toronto": "多伦多",
    "sydney": "悉尼",
    "australia": "澳大利亚"
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

def rename(line, index):
    latency = extract_latency(line)
    city = extract_city(line)
    if latency is None:
        return line
    return f"{line} #{index}-{city}-{latency}ms"

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    renamed = [rename(line, i + 1) for i, line in enumerate(lines)]

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed) + "\n")

if __name__ == "__main__":
    main()
