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

# Check etf spot data 
print("=== ETF spot (first 3) ===")
spot = run("curl -s 'http://localhost:8000/api/etf/spot?limit=3'")
print(spot[:500], flush=True)

# Check hk spot data
print("\n=== HK spot (first 3) ===")
spot = run("curl -s 'http://localhost:8000/api/hk/spot?limit=3'")
print(spot[:500], flush=True)

# Check stock spot for field names
print("\n=== Stock first item keys ===")
spot = run("curl -s 'http://localhost:8000/api/stock/spot?limit=1' | /usr/local/bin/python311 -c \"import sys,json; d=json.load(sys.stdin); item=d['data'][0]; print(type(item).__name__, list(item.keys())[:10] if isinstance(item,dict) else 'NOT DICT')\"")
print(spot, flush=True)

# Check ETF first item type
print("\n=== ETF first item type ===")
spot = run("curl -s 'http://localhost:8000/api/etf/spot?limit=1' | /usr/local/bin/python311 -c \"import sys,json; d=json.load(sys.stdin); item=d['data'][0]; print(type(item).__name__, item if not isinstance(item,dict) else list(item.keys())[:10])\"")
print(spot, flush=True)

ssh.close()
