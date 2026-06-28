import paramiko
import sys, os, time, json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'
REMOTE = '/opt/marketview'

print("Connecting...", flush=True)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)
print("Connected!", flush=True)

# Test command
stdin, stdout, stderr = ssh.exec_command("hostname")
print("hostname:", stdout.read().decode().strip(), flush=True)

# Push main.py
local_path = r'd:\服务器ETF\backend\main.py'
remote_path = f'{REMOTE}/backend/main.py'
print(f"Pushing {local_path} -> {remote_path}", flush=True)
sftp = ssh.open_sftp()
sftp.put(local_path, remote_path)
sftp.close()
print("Pushed OK", flush=True)

# Restart
print("Restarting marketview...", flush=True)
ssh.exec_command('systemctl restart marketview')
time.sleep(3)

stdin, stdout, stderr = ssh.exec_command('systemctl status marketview --no-pager | head -10')
print(stdout.read().decode(), flush=True)

# Wait 40s
print("Waiting 40s...", flush=True)
time.sleep(40)

# Health
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/api/health")
print("Health:", stdout.read().decode().strip(), flush=True)

# Batch
print("Triggering batch...", flush=True)
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=50'")
print("Batch response:", stdout.read().decode().strip(), flush=True)

# Wait 15s
print("Waiting 15s...", flush=True)
time.sleep(15)

# Rank
stdin, stdout, stderr = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'")
rank_out = stdout.read().decode().strip()
print("Rank response:", rank_out, flush=True)

# Parse
try:
    data = json.loads(rank_out)
    rank_count = len(data.get('data', []))
    print(f"Rank count: {rank_count}", flush=True)
except Exception as e:
    print(f"Parse error: {e}", flush=True)

ssh.close()
print("Done!", flush=True)
