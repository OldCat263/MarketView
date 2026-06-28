import paramiko
import os
import time

PASS = 'Qwe134679'
host = '43.156.133.37'
local = r'D:\服务器ETF\backend\fetcher\scorer.py'
remote = '/opt/marketview/backend/fetcher/scorer.py'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

# SFTP via paramiko
sftp = ssh.open_sftp()
sftp.put(local, remote)
sftp.close()
print('SFTP put OK')

_, o, _ = ssh.exec_command('systemctl restart marketview')
err = o.read().decode().strip()
print(f'restart: {err or "OK"}')

time.sleep(5)
print('--- verify ---')
_, o, _ = ssh.exec_command("curl -s http://localhost:8000/api/health | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:v for k,v in d.items()},indent=2))'")
print(o.read().decode(errors='replace')[:600])

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(f'predict status: {o.read().decode(errors="replace")[:100]}')

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=3'")
print(f'predict rank: {o.read().decode(errors="replace")[:300]}')

ssh.close()
