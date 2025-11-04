import os
import requests

def read_file(path):
    # 保留空行，只去除换行符
    with open(path, 'r', encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f]

wd = read_file('data/wd.txt')
dz_lines = read_file('data/dz.txt')

# 检查是否存在空行分隔符
if '' not in dz_lines:
    raise ValueError("dz.txt 缺少空行分隔符，请检查格式")

split_index = dz_lines.index('')
urls = dz_lines[:split_index]
repos = dz_lines[split_index+1:]

repo_txts = []
for repo in repos:
    try:
        repo_txts.append(requests.get(repo).text)
    except Exception as e:
        print(f"访问仓库失败: {repo} - {e}")

url_txts = []
for url in urls:
    try:
        url_txts.append(requests.get(url).text)
    except Exception as e:
        print(f"下载文件失败: {url} - {e}")

# 合并所有内容并去除空行
all_data = wd + url_txts + repo_txts
merged = '\n'.join([line for block in all_data for line in block.splitlines() if line.strip()])

# 写入根目录 v2.txt
with open('v2.txt', 'w', encoding='utf-8') as f:
    f.write(merged)
