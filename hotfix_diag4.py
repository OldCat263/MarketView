import paramiko
import sys, json

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

# Directly test _cached_get from within the running process
print("=== Testing _cached_get format via direct Python ===")
code = run("cd /opt/marketview/backend && /usr/local/bin/python311 -c \""
    "import json; "
    "from main import _cached_get; "
    "raw = _cached_get('stock'); "
    "print('Type:', type(raw)); "
    "print('Len:', len(raw) if raw else 0); "
    "print('First 200:', str(raw)[:200]); "
    "\" 2>&1")
print(code, flush=True)

# Also trigger batch for stock and check status after a while  
print("\n=== Triggering fresh batch ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'")
print(batch, flush=True)

import time
print("Waiting 60s...", flush=True)
time.sleep(60)

print("\n=== Status ===")
status = run("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(status, flush=True)

print("\n=== Rank ===")
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=5'")
print(rank[:500], flush=True)

ssh.close()
