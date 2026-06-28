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

# Check journalctl for errors
print("=== Journalctl (last 30 lines) ===")
log = run("journalctl -u marketview --no-pager -n 50 | tail -50")
print(log, flush=True)

print("\n=== Health ===")
health = run("curl -s http://localhost:8000/api/health")
print(health, flush=True)

# Try triggering batch with larger pool and more time
print("\n=== Triggering batch with pool_size=100 ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=100'")
print(batch, flush=True)

# Wait 60s
print("Waiting 60s...", flush=True)
time.sleep(60)

print("\n=== Fetching rank ===")
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
print(rank, flush=True)

try:
    data = json.loads(rank)
    print(f"Keys: {list(data.keys())}", flush=True)
    d = data.get('data', [])
    print(f"Data length: {len(d)}", flush=True)
    if len(d) > 0:
        print(f"First item: {d[0]}", flush=True)
except Exception as e:
    print(f"Parse error: {e}", flush=True)

ssh.close()
print("Done!", flush=True)
