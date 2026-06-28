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
    if err: print("STDERR:", err[:500], flush=True)
    return out.strip()

# Check ETF spot data for non-dict items
print("=== ETF spot first 30 items ===")
result = run("curl -s 'http://localhost:8000/api/etf/spot' | python3 -c "
    "\"import sys,json; d=json.load(sys.stdin); items=d['data']; "
    "print('len:', len(items)); "
    "bad=[(i,type(v).__name__,str(v)[:50]) for i,v in enumerate(items) if not isinstance(v,dict)]; "
    "print('bad:', bad[:5])\"")
print(result, flush=True)

# Also check: the ETF spot endpoint uses _ok which wraps in {'data': ...}
# But _cached_get returns the raw JSON list string.
# Let me verify: what does _cached_get actually return for ETF?
print("\n=== Testing _cached_get types ===")
result = run("cd /opt/marketview/backend && python3 -c \""
    "import json; from main import _cached_get; "
    "for m in ['stock','etf','hk']: "
    "    raw = _cached_get(m); "
    "    if raw and raw != '[]': "
    "        try: "
    "            d = json.loads(raw); "
    "            print(f'{m}: type={type(d).__name__} len={len(d)} first_type={type(d[0]).__name__ if d else \\\"empty\\\"}')"
    "        except Exception as e: print(f'{m}: parse error {e}')"
    "    else: print(f'{m}: empty')"
    "\"")
print(result, flush=True)

ssh.close()
