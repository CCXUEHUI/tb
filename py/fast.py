import os
import base64
import json
import re
import requests
from urllib.parse import urlparse

ORG = "socks-tjzjtm"
API_URL = f"https://api.github.com/orgs/{ORG}/repos"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
}

def get_all_repos():
    """
    分页获取组织的所有仓库，直到没有更多。
    """
    repos = []
    page = 1
    while True:
        resp = requests.get(API_URL, headers=HEADERS,
                            params={"per_page": 100, "page": page})
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def get_latest_repos(n=10):
    """
    获取最新更新的 n 个仓库。
    """
    repos = get_all_repos()
    # 按更新时间排序
    repos.sort(key=lambda r: r["updated_at"], reverse=True)
    names = [repo["name"] for repo in repos[:n]]
    print(f"Latest {len(names)} repos: {', '.join(names)}")
    return names

def get_repo_file_inner_text(repo):
    """
    每个仓库只有一个文件，该文件内容是 base64（外层）。
    文件内只有一行，这一行又是 base64（内层，订阅内容）。
    需要两次解码：外层 -> 单行 base64 -> 内层明文节点列表。
    """
    contents_url = f"https://api.github.com/repos/{ORG}/{repo}/contents"
    resp = requests.get(contents_url, headers=HEADERS)
    resp.raise_for_status()
    files = resp.json()

    if not isinstance(files, list) or len(files) < 1:
        print(f"  WARN: {repo} has no files.")
        return ""

    file_info = files[0]
    outer_encoded = file_info.get("content", "")
    if not outer_encoded:
        dl = file_info.get("download_url")
        if not dl:
            print(f"  WARN: {repo} file has neither content nor download_url.")
            return ""
        outer_text = requests.get(dl, headers=HEADERS).text
    else:
        outer_text = base64.b64decode(outer_encoded).decode("utf-8", errors="ignore")

    inner_line = outer_text.strip()
    if not inner_line:
        print(f"  WARN: {repo} outer decoded is empty.")
        return ""

    try:
        inner_text = base64.b64decode(inner_line).decode("utf-8", errors="ignore")
        return inner_text
    except Exception as e:
        print(f"  ERROR: {repo} inner base64 decode failed: {e}")
        return ""

def extract_node_name(node_str):
    """
    提取节点名称用于去重。
    """
    try:
        if node_str.startswith("vmess://"):
            payload = node_str[len("vmess://"):]
            decoded_json = base64.b64decode(payload).decode("utf-8", errors="ignore")
            data = json.loads(decoded_json)
            return data.get("ps", node_str)
        else:
            parsed = urlparse(node_str)
            if parsed.fragment:
                return parsed.fragment.strip()
            host = parsed.hostname or ""
            if host:
                return host.strip()
            m = re.search(r"#(.+)$", node_str)
            if m:
                return m.group(1).strip()
            return node_str
    except Exception:
        return node_str

def main():
    repos = get_latest_repos(60)  # 这里可以改成任意数量
    all_nodes = []
    seen_names = set()

    for repo in repos:
        print(f"Processing repository: {repo}")
        inner_text = get_repo_file_inner_text(repo)
        if not inner_text:
            continue

        lines = [ln.strip() for ln in inner_text.splitlines() if ln.strip()]
        print(f"  Decoded {len(lines)} inner lines from {repo}")

        added = 0
        for node in lines:
            name = extract_node_name(node)
            if name not in seen_names:
                seen_names.add(name)
                all_nodes.append(node)
                added += 1
        print(f"  Unique nodes added from {repo}: {added}")

    print(f"Total unique nodes collected: {len(all_nodes)}")

    with open("fast.txt", "w", encoding="utf-8") as f:
        for node in all_nodes:
            f.write(node + "\n")

    print("fast.txt updated successfully.")

if __name__ == "__main__":
    main()
