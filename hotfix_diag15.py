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
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip(): print("STDERR:", err.strip()[:500], flush=True)
    return out.strip()

# Write test script to server
run("cat > /tmp/test_cache.py << 'PYEOF'\n"
    "import json, sys\n"
    "sys.path.insert(0, '/opt/marketview/backend')\n"
    "from main import _cached_get\n"
    "for m in ['stock','etf','hk']:\n"
    "    raw = _cached_get(m)\n"
    "    print(f'{m}: raw_type={type(raw).__name__} raw_len={len(raw)} raw_start={raw[:80]}')\n"
    "    if raw and raw != '[]':\n"
    "        d = json.loads(raw)\n"
    "        print(f'  parsed_type={type(d).__name__} len={len(d)}')\n"
    "        if d:\n"
    "            first = d[0]\n"
    "            print(f'  first_type={type(first).__name__} keys={list(first.keys())[:5] if isinstance(first,dict) else first}')\n"
    "    else:\n"
    "        print(f'  EMPTY')\n"
    "PYEOF")

print("=== Cache types test ===")
result = run("cd /opt/marketview && python3 /tmp/test_cache.py")
print(result, flush=True)

ssh.close()
