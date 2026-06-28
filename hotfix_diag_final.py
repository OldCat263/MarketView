import paramiko
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Check all 50 items have '代码' field
script = '''import sys,json
d = json.load(sys.stdin)
items = d['data'][:50]
missing = sum(1 for r in items if not isinstance(r, dict) or '代码' not in r)
print(f"Total: {len(items)}, Missing 代码: {missing}")
if missing > 0:
    for i,r in enumerate(items):
        if not isinstance(r, dict) or '代码' not in r:
            print(f"  [{i}]: type={type(r).__name__}, val={str(r)[:80]}")
            break
'''
run(f"cat > /tmp/check_codes.py << 'PYEOF'\n{script}\nPYEOF")

print("=== Stock items ===")
result = run("curl -s 'http://localhost:8000/api/stock/spot?limit=50' | python3 /tmp/check_codes.py")
print(result, flush=True)

print("\n=== ETF items ===")
result = run("curl -s 'http://localhost:8000/api/etf/spot?limit=50' | python3 /tmp/check_codes.py")
print(result, flush=True)

print("\n=== HK items ===")
result = run("curl -s 'http://localhost:8000/api/hk/spot?limit=50' | python3 /tmp/check_codes.py")
print(result, flush=True)

ssh.close()
