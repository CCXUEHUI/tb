import re
import socket
import time
import threading
import requests
from queue import Queue

INPUT_FILE = 'v2.txt'
MAX_THREADS = 50
TEST_PORT = 443
TEST_TIMEOUT = 3
TOP_NODES = 30

# 正则提取协议和域名/IP
NODE_REGEX = re.compile(r'^(?P<protocol>vless|vmess|trojan|ss)://(?P<rest>.+)', re.IGNORECASE)
HOST_REGEX = re.compile(r'@(?P<host>[^:]+)')

def extract_info(line):
    match = NODE_REGEX.match(line)
    if not match:
        return None, None
    protocol = match.group('protocol').upper()
    rest = match.group('rest')
    host_match = HOST_REGEX.search(rest)
    host = host_match.group('host') if host_match else None
    return protocol, host

def test_latency(host):
    try:
        start = time.time()
        with socket.create_connection((host, TEST_PORT), timeout=TEST_TIMEOUT):
            return int((time.time() - start) * 1000)
    except Exception:
        return None

def get_location(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city", timeout=5)
        data = r.json()
        city = data.get('city') or data.get('country') or '未知'
        return city
    except Exception:
        return '未知'

class NodeTester:
    def __init__(self):
        self.nodes = []
        self.results = []
        self.lock = threading.Lock()

    def load_nodes(self):
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                protocol, host = extract_info(line)
                if host:
                    self.nodes.append((line, protocol, host))

    def worker(self, queue):
        while not queue.empty():
            line, protocol, host = queue.get()
            latency = test_latency(host)
            location = get_location(host)
            with self.lock:
                self.results.append((line, protocol, host, latency, location))
            queue.task_done()

    def run(self):
        self.load_nodes()
        queue = Queue()
        for item in self.nodes:
            queue.put(item)

        threads = []
        for _ in range(min(MAX_THREADS, len(self.nodes))):
            t = threading.Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.results.sort(key=lambda x: x[3] if x[3] is not None else float('inf'))
        self.save_top_nodes()

    def save_top_nodes(self):
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            for idx, (line, protocol, host, latency, location) in enumerate(self.results[:TOP_NODES], 1):
                tag = f"{latency}ms" if latency is not None else "timeout"
                new_name = f"{idx:02d}_{location}_{tag}"
                if '#' in line:
                    line = re.sub(r'#.*$', f'#{new_name}', line)
                else:
                    line += f'#{new_name}'
                f.write(line + '\n')

if __name__ == "__main__":
    tester = NodeTester()
    tester.run()
