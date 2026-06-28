import paramiko
import sys, time

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

# Check precompute output from startup (within 5 minutes ago)
print("=== Startup precompute logs ===")
log = run("journalctl -u marketview --no-pager --since '10 min ago' | grep -i 'Preload\|precompute\|ranked\|predict/'")
print(log if log else "(no precompute entries)", flush=True)

# Also check for any error during initial batch
print("\n=== Any errors in logs ===")
log = run("journalctl -u marketview --no-pager --since '10 min ago' | grep -i 'error\|traceback\|exception' | tail -20")
print(log if log else "(no errors)", flush=True)

# Try the batch with longer wait and check logs immediately after
print("\n=== Triggering batch stock pool_size=30, waiting 120s ===")
batch = run("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=30'")
print(batch, flush=True)

time.sleep(120)

print("\n=== Status after 120s ===")
status = run("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(status, flush=True)

print("\n=== Rank ===")
rank = run("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=5'")
print(rank, flush=True)

print("\n=== Recent logs for predict/batch ===")
log = run("journalctl -u marketview --no-pager --since '2 min ago' | grep -i 'predict\|batch\|scorer\|rank_batch\|error\|exception' | tail -20")
print(log if log else "(no entries)", flush=True)

ssh.close()
