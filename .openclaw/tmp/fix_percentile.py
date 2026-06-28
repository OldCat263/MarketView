import paramiko
from scp import SCPClient
import os

PASS = 'Qwe134679'
host = '43.156.133.37'
local = r'D:\服务器ETF\backend\fetcher\scorer.py'
remote = '/opt/marketview/backend/fetcher/scorer.py'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

with SCPClient(ssh.get_transport()) as scp:
    scp.put(local, remote)
print('SCP OK')

_, o, _ = ssh.exec_command('systemctl restart marketview')
err = o.read().decode().strip()
print(f'restart: {err or "OK"}')

import time
time.sleep(3)
print('--- verify ---')
_, o, _ = ssh.exec_command("curl -s http://localhost:8000/api/health | python -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:v for k,v in d.items()},indent=2))' 2>&1")
print(o.read().decode(errors='replace')[:500])

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(f'predict status: {o.read().decode(errors="replace")[:100]}')

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=3'")
print(f'predict rank: {o.read().decode(errors="replace")[:200]}')

ssh.close()
