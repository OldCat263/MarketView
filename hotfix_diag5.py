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

# Check the stock spot endpoint implementation
print("=== Stock spot endpoint ===")
code = run("sed -n '263,275p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Check what _ok does with the response
print("\n=== _ok function ===")
code = run("sed -n '248,262p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Test the spot endpoint directly
print("\n=== curl stock/spot ===")
spot = run("curl -s 'http://localhost:8000/api/stock/spot?limit=3'")
print(spot[:300], flush=True)

# Test through API 
print("\n=== curl data module stock ===")
data = run("curl -s 'http://localhost:8000/api/data/stock?limit=3'")
print(data[:300] if data else "(empty)", flush=True)

ssh.close()
