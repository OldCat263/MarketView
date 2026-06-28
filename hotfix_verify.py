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

# Wait more
print("Waiting 60s for modules to load...", flush=True)
time.sleep(60)

# Health
health = run("curl -s http://localhost:8000/api/health")
print("Health:", health, flush=True)

# Trigger batch again
print("Triggering batch again...", flush=True)
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'")
print("Batch:", batch, flush=True)

# Wait 30s this time
print("Waiting 30s...", flush=True)
time.sleep(30)

# Rank
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
print("Rank:", rank, flush=True)

try:
    data = json.loads(rank)
    rank_count = len(data.get('data', []))
    print(f"Rank count: {rank_count}", flush=True)
except Exception as e:
    print(f"Parse error: {e}", flush=True)

ssh.close()
print("Done!", flush=True)
