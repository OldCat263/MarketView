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

# First check current health
print("=== Health ===")
h = run("curl -s http://localhost:8000/api/health")
print(h, flush=True)

# Trigger batch and wait longer
print("\n=== Triggering batch stock pool_size=200 ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=200'")
print(batch, flush=True)

# Wait 90s for compute
print("Waiting 90s for batch compute...", flush=True)
time.sleep(30)
print("...30s", flush=True)
time.sleep(30)
print("...60s", flush=True)

# Check logs for progress
print("\n=== Predict-related logs ===")
log = run("journalctl -u marketview --no-pager --since '90 sec ago' | grep -i -E 'predict|batch|precompute|scored|scoring|rank|error|exception|traceback' | tail -15")
print(log if log else "(no entries)", flush=True)

time.sleep(30)
print("...90s done", flush=True)

# Check rank
print("\n=== Fetching rank ===")
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
print(rank, flush=True)

try:
    data = json.loads(rank)
    d = data.get('data', [])
    print(f"Data count: {len(d)}", flush=True)
    if len(d) > 0 and len(d) >= 1:
        print(f"Top item: {json.dumps(d[0], ensure_ascii=False)}", flush=True)
except Exception as e:
    print(f"Parse error: {e}", flush=True)

ssh.close()
print("Done!", flush=True)
