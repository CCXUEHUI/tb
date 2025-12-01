import requests
import base64
import os

ORG = "socks-tjzjtm"
API_URL = f"https://api.github.com/orgs/{ORG}/repos"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"  # 使用 Actions 内置 Token
}

def get_latest_repos(n=10):
    repos = requests.get(API_URL, headers=HEADERS,
                         params={"per_page": n, "sort": "updated", "direction": "desc"}).json()
    return [repo["name"] for repo in repos]

def get_single_file_content(repo):
    contents_url = f"https://api.github.com/repos/{ORG}/{repo}/contents"
    files = requests.get(contents_url, headers=HEADERS).json()
    if isinstance(files, list) and len(files) >= 1:
        file_info = files[0]
        encoded = file_info.get("content", "")
        if encoded:
            # GitHub API 返回的 content 是 base64 编码
            decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")
            return decoded
        elif "download_url" in file_info:
            raw = requests.get(file_info["download_url"], headers=HEADERS).text
            return raw
    return ""

def main():
    repos = get_latest_repos(10)
    all_nodes = []

    for repo in repos:
        print(f"Processing repository: {repo}")
        content = get_single_file_content(repo)
        repo_nodes = [line.strip() for line in content.splitlines() if line.strip()]
        print(f"  Decoded {len(repo_nodes)} nodes from {repo}")
        all_nodes.extend(repo_nodes)

    # 去重
    unique_nodes = sorted(set(all_nodes))
    print(f"Total unique nodes collected: {len(unique_nodes)}")

    # 写入 fast.txt
    with open("fast.txt", "w", encoding="utf-8") as f:
        for node in unique_nodes:
            f.write(node + "\n")
    print("fast.txt updated successfully.")

if __name__ == "__main__":
    main()
