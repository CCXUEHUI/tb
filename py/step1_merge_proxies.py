import requests
from bs4 import BeautifulSoup

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f]

def extract_root_txt_links(repo_url):
    try:
        html = requests.get(repo_url).text
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.select('a.js-navigation-open')
        txt_files = []
        for link in links:
            href = link.get('href', '')
            if href.endswith('.txt') and href.count('/') == 5:
                # 只提取根路径下的 txt 文件（路径层级为 5）
                parts = href.split('/')
                if 'blob' in parts:
                    blob_index = parts.index('blob')
                    raw_url = f"https://raw.githubusercontent.com/{parts[1]}/{parts[2]}/{'/'.join(parts[blob_index+1:])}"
                    txt_files.append(raw_url)
        return txt_files
    except Exception as e:
        print(f"解析仓库失败: {repo_url} - {e}")
        return []

# 读取本地代理节点
wd = read_file('data/wd.txt')

# 读取下载链接和仓库地址
dz_lines = read_file('data/dz.txt')
if '' not in dz_lines:
    raise ValueError("dz.txt 缺少空行分隔符")

split_index = dz_lines.index('')
urls = dz_lines[:split_index]
repos = dz_lines[split_index+1:]

# 下载仓库中的 txt 文件内容
repo_txts = []
for repo in repos:
    txt_links = extract_root_txt_links(repo)
    for txt_url in txt_links:
        try:
            repo_txts.append(requests.get(txt_url).text)
        except Exception as e:
            print(f"下载失败: {txt_url} - {e}")

# 下载指定链接中的 txt 内容
url_txts = []
for url in urls:
    try:
        url_txts.append(requests.get(url).text)
    except Exception as e:
        print(f"下载失败: {url} - {e}")

# 合并所有内容并去除空行
all_data = wd + url_txts + repo_txts
merged = '\n'.join([line for block in all_data for line in block.splitlines() if line.strip()])

# 写入 v2.txt
with open('v2.txt', 'w', encoding='utf-8') as f:
    f.write(merged)
