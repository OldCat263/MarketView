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

# Use python311
result = run("cd /opt/marketview/backend && /usr/local/bin/python311 -c \""
    "import json; from main import _cached_get; "
    "for m in ['stock','etf','hk']: "
    "    raw = _cached_get(m); "
    "    print(f'{m}: raw_type={type(raw).__name__} raw_len={len(raw)}'); "
    "    if raw and raw != '[]': "
    "        d = json.loads(raw); "
    "        print(f'  parsed: type={type(d).__name__} len={len(d)}'); "
    "        if d: "
    "            first = d[0]; "
    "            if isinstance(first, dict): "
    "                print(f'  first: keys={list(first.keys())[:5]}'); "
    "            else: "
    "                print(f'  first: type={type(first).__name__} val={first}'); "
    "    else: print('  EMPTY'); "
    "\" 2>&1")
print("=== Cache types ===")
print(result, flush=True)

ssh.close()
