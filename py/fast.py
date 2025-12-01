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

def get_latest_repos(n=60):
    repos = []
    page = 1
    while len(repos) < n:
        resp = requests.get(API_URL, headers=HEADERS,
                    params={"per_page": 100, "page": 1,
                            "sort": "updated", "direction": "desc"})
        print(len(resp.json()))

        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend([repo["name"] for repo in batch])
        page += 1
    return repos[:n]


def get_repo_file_inner_text(repo):
    """
    每个仓库只有一个文件，该文件内容通过 GitHub API 返回为 base64（外层）。
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
        # fallback: download_url（但通常 content 会存在）
        dl = file_info.get("download_url")
        if not dl:
            print(f"  WARN: {repo} file has neither content nor download_url.")
            return ""
        outer_text = requests.get(dl, headers=HEADERS).text
    else:
        # 外层 base64 -> 得到单行内层 base64
        outer_text = base64.b64decode(outer_encoded).decode("utf-8", errors="ignore")

    inner_line = outer_text.strip()
    if not inner_line:
        print(f"  WARN: {repo} outer decoded is empty.")
        return ""

    # 内层 base64 -> 明文节点列表（多行）
    try:
        inner_text = base64.b64decode(inner_line).decode("utf-8", errors="ignore")
        return inner_text
    except Exception as e:
        print(f"  ERROR: {repo} inner base64 decode failed: {e}")
        return ""

def extract_node_name(node_str):
    """
    提取节点名称用于去重：
    - vmess://base64(JSON) -> JSON 中的 'ps'
    - vless/trojan/ss/hysteria URI -> 使用 #fragment 作为名称；若无则使用 host 作为回退
    - 其他协议 -> 使用 #fragment 或整行
    """
    try:
        if node_str.startswith("vmess://"):
            payload = node_str[len("vmess://"):]
            decoded_json = base64.b64decode(payload).decode("utf-8", errors="ignore")
            data = json.loads(decoded_json)
            name = data.get("ps")
            if name:
                return name.strip()
            # 回退：host 或整行
            host = data.get("add") or ""
            return host.strip() or node_str
        else:
            # 通用 URI 解析
            parsed = urlparse(node_str)
            if parsed.fragment:
                return parsed.fragment.strip()
            # 某些 ss 可能是 ss://method:pass@host:port，没有 fragment；用 host 作为回退
            host = parsed.hostname or ""
            if host:
                return host.strip()
            # 再回退：如果是形如 "...#name" 手动正则抓取
            m = re.search(r"#(.+)$", node_str)
            if m:
                return m.group(1).strip()
            return node_str
    except Exception:
        return node_str

def main():
    repos = get_latest_repos(10)
    all_nodes = []
    seen_names = set()

    for repo in repos:
        print(f"Processing repository: {repo}")
        inner_text = get_repo_file_inner_text(repo)
        if not inner_text:
            print(f"  WARN: {repo} produced empty inner text.")
            continue

        lines = [ln.strip() for ln in inner_text.splitlines() if ln.strip()]
        print(f"  Decoded inner lines: {len(lines)}")

        added = 0
        for node in lines:
            name = extract_node_name(node)
            if name not in seen_names:
                seen_names.add(name)
                all_nodes.append(node)  # 写入明文节点（不再 base64）
                added += 1
        print(f"  Unique by name added from {repo}: {added}")

    print(f"Total unique nodes collected (by name): {len(all_nodes)}")

    # 写入 fast.txt（在所有处理完成后统一写入）
    with open("fast.txt", "w", encoding="utf-8") as f:
        for node in all_nodes:
            f.write(node + "\n")

    print("fast.txt updated successfully with plain decoded nodes.")

if __name__ == "__main__":
    main()
