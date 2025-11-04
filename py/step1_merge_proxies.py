import requests
import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_raw_txt_from_repo(repo_url):
    try:
        html = requests.get(repo_url).text
        # 匹配根目录下的 .txt 文件链接（只匹配 blob/main/*.txt）
        matches = re.findall(r'href="(/[^/]+/[^/]+/blob/[^/]+/[^/]+\.txt)"', html)
        for href in matches:
            parts = href.split('/')
            if len(parts) == 5:  # 只处理根目录文件
                raw_url = f"https://raw.githubusercontent.com/{parts[1]}/{parts[2]}/{parts[3]}/{parts[4]}"
                try:
                    return requests.get(raw_url).text
                except Exception as e:
                    print(f"下载失败: {raw_url} - {e}")
        print(f"仓库中未找到根目录下的 .txt 文件: {repo_url}")
        return ''
    except Exception as e:
        print(f"访问仓库失败: {repo_url} - {e}")
        return ''

def get_txt_from_raw_url(url):
    try:
        return requests.get(url).text
    except Exception as e:
        print(f"下载失败: {url} - {e}")
        return ''

# 读取 wd.txt 和 dz.txt
wd = read_file('data/wd.txt')
dz = read_file('data/dz.txt')

# 合并所有内容
all_data = wd[:]

for line in dz:
    if line.startswith('https://raw.githubusercontent.com/'):
        content = get_txt_from_raw_url(line)
        all_data.append(content)
    elif line.startswith('https://github.com/'):
        content = get_raw_txt_from_repo(line)
        all_data.append(content)
    else:
        print(f"未知地址格式，跳过: {line}")

# 去除空行并写入 v2.txt
merged = '\n'.join([line for block in all_data for line in block.splitlines() if line.strip()])
with open('v2.txt', 'w', encoding='utf-8') as f:
    f.write(merged)
