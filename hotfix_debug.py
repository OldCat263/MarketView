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

# Write a debug script that mimics what _do_batch does
script = '''
import json, sys
sys.path.insert(0, '/opt/marketview/backend')
from main import _cached_get, _CODE_PREFIX

module = 'stock'
pool_size = 50

raw = _cached_get(module)
print(f"raw type: {type(raw).__name__}")
print(f"raw == '[]': {raw == '[]'}")
print(f"raw[:200]: {raw[:200]}")

spot_data = json.loads(raw)
print(f"spot_data type: {type(spot_data).__name__}")
print(f"spot_data is dict: {isinstance(spot_data, dict)}")
print(f"spot_data is list: {isinstance(spot_data, list)}")
if isinstance(spot_data, list):
    print(f"spot_data len: {len(spot_data)}")
    if spot_data:
        first = spot_data[0]
        print(f"first item type: {type(first).__name__}")
        if isinstance(first, dict):
            print(f"first keys[:10]: {list(first.keys())[:10]}")
            code = first.get('代码', '')
            print(f"code field: '{code}'")
        else:
            print(f"first item value: {first}")

items = spot_data.get('data', spot_data) if isinstance(spot_data, dict) else spot_data
print(f"items type: {type(items).__name__}")
print(f"items is list: {isinstance(items, list)}")

codes = []
if isinstance(items, list):
    for r in items[:pool_size]:
        c = r.get('代码', r.get('交易对', ''))
        if c:
            pf = _CODE_PREFIX.get(module)
            codes.append(pf(c) if pf else c)
        else:
            print(f"  NO CODE for item: {type(r).__name__} = {str(r)[:50]}")
print(f"codes count: {len(codes)}")
if codes:
    print(f"first 5 codes: {codes[:5]}")
'''

run("cat > /tmp/test_batch.py << 'PYEOF'\n" + script + "PYEOF")
result = run("/usr/local/bin/python311 /tmp/test_batch.py 2>&1")
print("=== Batch test ===")
print(result, flush=True)

ssh.close()
