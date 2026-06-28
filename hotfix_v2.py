import paramiko
import sys, os, time, json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'
REMOTE = '/opt/marketview'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
print("Connected!", flush=True)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Push main.py
local_path = r'd:\服务器ETF\backend\main.py'
remote_path = f'{REMOTE}/backend/main.py'
print(f"Pushing {local_path}...", flush=True)
sftp = ssh.open_sftp()
sftp.put(local_path, remote_path)
sftp.close()
print("Pushed!", flush=True)

# Restart
print("Restarting...", flush=True)
run("systemctl restart marketview")
time.sleep(5)
print(run("systemctl status marketview --no-pager | head -5"), flush=True)

# Wait 120s
print("Waiting 120s for init...", flush=True)
for i in range(120, 0, -20):
    time.sleep(20)
    h = run("curl -s http://localhost:8000/api/health")
    print(f"  t={120-i}s: {h}", flush=True)

# Trigger batch
print("\nTriggering batch stock...", flush=True)
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'")
print(batch, flush=True)

# Wait 120s
print("Waiting 120s for batch...", flush=True)
time.sleep(120)

# Rank
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
print(f"Rank: {rank[:500]}", flush=True)

try:
    data = json.loads(rank)
    count = len(data.get('data', []))
    print(f"\nRank count: {count}", flush=True)
except:
    pass

# Check debug logs
print("\n=== Predict debug logs ===")
log = run("journalctl -u marketview --no-pager --since '5 min ago' -o cat | grep -E 'Preload.*predict|batch/' | tail -15")
print(log, flush=True)

ssh.close()
print("Done!", flush=True)
