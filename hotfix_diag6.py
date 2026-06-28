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

# Show the rest of _cached_get (the list merging part)
print("=== Full _cached_get ===")
code = run("sed -n '69,120p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Also check: what does _cached_get return for stock via direct API
# Run this on the server: check the raw return
print("\n=== Direct _cached_get length check ===")
result = run("cd /opt/marketview/backend && /usr/local/bin/python311 -c \""
    "import json, time; "
    "# Wait for data to be available; "
    "time.sleep(2); "
    "from main import _cached_get, _cache; "
    "# Show cache keys and their contents; "
    "print('Cache keys:', list(_cache.keys())); "
    "for k in _cache: "
    "    shards = _cache[k].get('shards', {}); "
    "    for si, sd in sorted(shards.items()): "
    "        d = sd.get('data'); "
    "        t = type(d).__name__; "
    "        l = len(d) if d else 0; "
    "        print(f'  {k} shard {si}: {t} len={l}'); "
    "\" 2>&1")
print(result, flush=True)

ssh.close()
