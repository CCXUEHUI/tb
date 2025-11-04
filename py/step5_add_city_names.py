import ipaddress
import requests

def get_city(ip):
    try:
        r = requests.get(f'https://ipapi.co/{ip}/city/')
        return r.text.strip()
    except:
        return '未知'

with open('v2.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

new_lines = []
for line in lines:
    parts = line.split('|')
    if len(parts) == 2:
        name, addr = parts
        ip = addr.split(':')[0]
        city = get_city(ip)
        new_lines.append(f"{city}-{name}")

with open('v2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
