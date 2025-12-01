import urllib.request
import json
import base64

ORG = "socks-tjzjtm"
API_URL = f"https://api.github.com/orgs/{ORG}/repos"

def fetch_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def get_latest_repos(n=10):
    repos = fetch_json(f"{API_URL}?per_page={n}&sort=updated&direction=desc")
    return [repo["name"] for repo in repos]

def get_single_file_content(repo):
    contents_url = f"https://api.github.com/repos/{ORG}/{repo}/contents"
    files = fetch_json(contents_url)
    if isinstance(files, list) and len(files) == 1:
        encoded = files[0]["content"]
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
    with open("fast.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(nodes)))

if __name__ == "__main__":
    main()
