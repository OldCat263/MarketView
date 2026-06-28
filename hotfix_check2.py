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

# Search for predict-related function defs
print("=== All predict function defs ===")
code = run("grep -n 'async def.*predict\|def.*predict\|def.*precompute\|def.*batch' /opt/marketview/backend/main.py")
print(code, flush=True)

# Show the batch endpoint  
print("\n=== Around batch endpoint ===")
code = run("grep -n -A10 'predict/batch' /opt/marketview/backend/main.py")
print(code, flush=True)

# Show the rank endpoint
print("\n=== Around rank endpoint ===")
code = run("grep -n -A15 'predict/rank' /opt/marketview/backend/main.py")
print(code, flush=True)

ssh.close()
