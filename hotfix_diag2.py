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

# Check predict status
print("=== Predict status ===")
status = run("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(status, flush=True)

# Check spot data for stock
print("\n=== Spot data for stock (first 500 chars) ===")
spot = run("curl -s 'http://localhost:8000/api/spot/stock?limit=3'")
print(spot[:500], flush=True)

# Also check _cached_get format by looking at how it's called
print("\n=== _cached_get function ===")
code = run("grep -A10 'def _cached_get' /opt/marketview/backend/main.py")
print(code, flush=True)

# Check what the etf predict status is
print("\n=== ETF predict status ===")
status = run("curl -s 'http://localhost:8000/api/predict/status/etf'")
print(status, flush=True)

ssh.close()
