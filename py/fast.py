import requests
import base64
import os

ORG = "socks-tjzjtm"
API_URL = f"https://api.github.com/orgs/{ORG}/repos"
HEADERS = {
    "Accept": "application/vnd.github+json",
    # 使用 GitHub Actions 提供的 GITHUB_TOKEN，避免限流
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
}

def get_latest_repos(n=10):
    repos = requests.get(API_URL, headers=HEADERS, params={"per_page": n, "sort": "updated", "direction": "desc"}).json()
    return [repo["name"] for repo in repos]

def get_single_file_content(repo):
    contents_url = f"https://api.github.com/repos/{ORG}/{repo}/contents"
    files = requests.get(contents_url, headers=HEADERS).json()
    if isinstance(files, list) and len(files) >= 1:
        # 取第一个文件
        file_info = files[0]
        if "content" in file_info and file_info["content"]:
            encoded = file_info["content"]
            return base64.b64decode(encoded).decode("utf-8", errors="ignore")
        elif "download_url" in file_info:
            raw = requests.get(file_info["download_url"], headers=HEADERS).text
            return raw
    return ""

def main():
    repos = get_latest_repos(10)
    nodes = set()
    for repo in repos:
        content = get_single_file_content(repo)
        for line in content.splitlines():
            if line.strip():
                nodes.add(line.strip())
    with open("fast.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(nodes)))

if __name__ == "__main__":
    main()
