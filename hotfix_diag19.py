import paramiko
import sys, time

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
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out.strip()

print("=== Current health ===")
h = run("curl -s http://localhost:8000/api/health")
print(h, flush=True)

# Let's try: run the predict synchronously by directly calling the scorer from the server
print("\n=== Direct scorer test ===")
result = run("cd /opt/marketview/backend && /usr/local/bin/python311 << 'PYEOF'\n"
    "import json, sys\n"
    "sys.path.insert(0, '.')\n"
    "from fetcher.scorer import rank_batch\n\n"
    "# Test with a few known stock codes\n"
    "codes = ['sh600519', 'sz000001', 'sh600036', 'sz000858', 'sh601318']\n"
    "print(f'Testing rank_batch with codes: {codes}')\n"
    "results = rank_batch('stock', codes, '1d', 'quick', max_workers=3)\n"
    "print(f'Results count: {len(results)}')\n"
    "if results:\n"
    "    print(f'First result: {json.dumps(results[0], ensure_ascii=False)[:200]}')\n"
    "PYEOF")
print(result, flush=True)

ssh.close()
