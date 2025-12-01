import requests
import base64

ORG = "socks-tjzjtm"
API_URL = f"https://api.github.com/orgs/{ORG}/repos"
HEADERS = {"Accept": "application/vnd.github+json"}

def get_latest_repos(n=10):
    # 获取仓库列表，按更新时间倒序
    repos = requests.get(API_URL, headers=HEADERS, params={"per_page": n, "sort": "updated", "direction": "desc"}).json()
    return [repo["name"] for repo in repos]

def get_single_file_content(repo):
    # 获取仓库内容（假设只有一个文件）
    contents_url = f"https://api.github.com/repos/{ORG}/{repo}/contents"
    files = requests.get(contents_url, headers=HEADERS).json()
    if isinstance(files, list) and len(files) == 1:
        file_info = files[0]
        encoded = file_info.get("content", "")
        if encoded:
            return base64.b64decode(encoded).decode("utf-8", errors="ignore")
    return ""

def main():
    repos = get_latest_repos(10)
    nodes = set()
    for repo in repos:
        content = get_single_file_content(repo)
        for line in content.splitlines():
            if line.strip():
                nodes.add(line.strip())
    # 写入 fast.txt
    with open("fast.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(nodes)))

if __name__ == "__main__":
    main()
