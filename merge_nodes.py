# merge_nodes.py
# ✅ 节点重命名：根据顺序添加编号标签

def rename(line, index):
    if line.startswith("vmess://") or line.startswith("vless://") or line.startswith("trojan://"):
        return line + f" #节点{index:02d}"
    return line

def main():
    with open("v2.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    renamed = [rename(line, i + 1) for i, line in enumerate(lines)]

    with open("v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed) + "\n")

if __name__ == "__main__":
    main()
