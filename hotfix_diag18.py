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

# Get ALL precompute predict logs
print("=== All predict precompute logs ===")
result = run("journalctl -u marketview --no-pager --since '20 min ago' -o cat | grep 'predict/'")
print(result, flush=True)

# Also look for stock precompute specifically
print("\n=== Stock predict errors ===")
result = run("journalctl -u marketview --no-pager --since '20 min ago' -o cat | grep -i 'predict/stock'")
print(result if result else "(none)", flush=True)

# Check predict status for all modules
print("\n=== Predict statuses ===")
for m in ['stock', 'etf', 'hk', 'us', 'index']:
    status = run(f"curl -s 'http://localhost:8000/api/predict/status/{m}'")
    print(f"  {m}: {status}", flush=True)

ssh.close()
