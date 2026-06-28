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

# Check logs for predict-related entries + errors
print("=== Predict-related logs ===")
log = run("journalctl -u marketview --no-pager --since '1 min ago' | grep -i -E 'predict|error|traceback|exception|precompute|scorer' | tail -40")
print(log if log else "(no predict entries)", flush=True)

print("\n=== Recent log tail ===")
log = run("journalctl -u marketview --no-pager --since '2 min ago' | tail -30")
print(log if log else "(empty)", flush=True)

# Also try etf module which loaded fine
print("\n=== Trying ETF batch ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/etf?pool_size=50'")
print(batch, flush=True)

time.sleep(30)
rank = run("curl -s 'http://localhost:8000/api/predict/rank/etf?period=1d&limit=10'")
print("ETF rank:", rank[:500], flush=True)

try:
    data = json.loads(rank)
    print(f"ETF data count: {len(data.get('data',[]))}", flush=True)
except:
    pass

ssh.close()
print("Done!", flush=True)
