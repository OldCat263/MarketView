import paramiko
import sys, time, json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

print("Connecting...", flush=True)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
print("Connected!", flush=True)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Check that the hotfix code is actually in main.py on the server
print("=== Checking main.py for _CODE_PREFIX ===")
code = run("grep -n '_CODE_PREFIX\|_stock_prefix\|isinstance' /opt/marketview/backend/main.py | head -20")
print(code if code else "(NOT FOUND)", flush=True)

print("\n=== Checking predict_batch function ===")
code = run("grep -A5 'async def predict_batch' /opt/marketview/backend/main.py")
print(code if code else "(NOT FOUND)", flush=True)

# Check precompute_predict
print("\n=== Checking _precompute_predict ===")
code = run("grep -A15 'async def _precompute_predict' /opt/marketview/backend/main.py")
print(code if code else "(NOT FOUND)", flush=True)

# Now try to directly run the predict computation synchronously from Python  
print("\n=== Attempting direct predict compute ===")
result = run("cd /opt/marketview/backend && /usr/local/bin/python311 -c \""
    "import asyncio, json; "
    "from main import app; "
    "print('app loaded'); "
    "\" 2>&1 | tail -5")
print(result, flush=True)

ssh.close()
print("Done!", flush=True)
