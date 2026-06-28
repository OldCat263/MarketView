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

# Check _load_one function
print("=== _load_one function ===")
code = run("sed -n '160,190p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Check what the index spot data looks like (it was the only one that worked)
print("\n=== Index spot (first 500 chars) ===")
spot = run("curl -s 'http://localhost:8000/api/index/spot'")
print(spot[:500], flush=True)

ssh.close()
