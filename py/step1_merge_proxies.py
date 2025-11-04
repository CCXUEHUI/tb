import os
import requests

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

wd = read_file('data/wd.txt')
dz_lines = read_file('data/dz.txt')

split_index = dz_lines.index('')
urls = dz_lines[:split_index]
repos = dz_lines[split_index+1:]

repo_txts = []
for repo in repos:
    try:
        repo_txts.append(requests.get(repo).text)
    except:
        pass

url_txts = []
for url in urls:
    try:
        url_txts.append(requests.get(url).text)
    except:
        pass

all_data = wd + url_txts + repo_txts
merged = '\n'.join([line for block in all_data for line in block.splitlines() if line.strip()])

with open('v2.txt', 'w', encoding='utf-8') as f:
    f.write(merged)
