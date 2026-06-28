import paramiko
import sys, time, json

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

print("=== Restarting ===")
run("systemctl restart marketview")
time.sleep(5)
status = run("systemctl status marketview --no-pager | head -5")
print(status, flush=True)

print("\n=== Waiting 120s for full initialization ===")
for i in range(120, 0, -10):
    time.sleep(10)
    if i % 30 == 0:
        h = run("curl -s http://localhost:8000/api/health")
        print(f"  t={120-i}s: {h}", flush=True)

print("\n=== Health ===")
h = run("curl -s http://localhost:8000/api/health")
print(h, flush=True)

print("\n=== Triggering batch stock ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'")
print(batch, flush=True)

print("\n=== Waiting 120s for batch ===")
time.sleep(120)

print("\n=== Status ===")
status = run("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(status, flush=True)

print("\n=== Rank ===")
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
print(rank[:800], flush=True)

try:
    data = json.loads(rank)
    count = len(data.get('data', []))
    print(f"\nRank count: {count}", flush=True)
    if count > 0:
        print("SUCCESS!", flush=True)
except:
    pass

print("\n=== Precompute logs ===")
log = run("journalctl -u marketview --no-pager --since '3 min ago' -o cat | grep 'predict/' | tail -10")
print(log, flush=True)

ssh.close()
