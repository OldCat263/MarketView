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

# Check if any items are not dicts
print("=== ETF data item types ===")
result = run("curl -s 'http://localhost:8000/api/etf/spot?limit=100' | /usr/local/bin/python311 -c \""
    "import sys,json; "
    "d=json.load(sys.stdin); "
    "items=d['data']; "
    "types = {}; "
    "for i,item in enumerate(items): "
    "    t = type(item).__name__; "
    "    types[t] = types.get(t,0)+1; "
    "    if t != 'dict': print(f'  index {i}: {t} = {item}'); "
    "print('Type counts:', types); "
    "print('Total items:', len(items))\"")
print(result, flush=True)

# Check HK
print("\n=== HK data item types ===")
result = run("curl -s 'http://localhost:8000/api/hk/spot?limit=100' | /usr/local/bin/python311 -c \""
    "import sys,json; "
    "d=json.load(sys.stdin); "
    "items=d['data']; "
    "types = {}; "
    "for i,item in enumerate(items): "
    "    t = type(item).__name__; "
    "    types[t] = types.get(t,0)+1; "
    "    if t != 'dict': print(f'  index {i}: {t} = {repr(item)[:80]}'); "
    "print('Type counts:', types); "
    "print('Total items:', len(items))\"")
print(result, flush=True)

ssh.close()
