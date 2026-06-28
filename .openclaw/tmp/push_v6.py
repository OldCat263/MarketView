# -*- coding: utf-8 -*-
import paramiko, json, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Just push the file
with open(r'D:\服务器ETF\backend\fetcher\us.py', 'r', encoding='utf-8') as f:
    local = f.read()

sftp = ssh.open_sftp()
with sftp.open('/opt/marketview/backend/fetcher/us.py', 'w') as f:
    f.write(local)
sftp.close()
print('pushed')

# Verify no Tencent in code
_, o, _ = ssh.exec_command("grep -c 'Tencent' /opt/marketview/backend/fetcher/us.py 2>/dev/null || echo 0")
tcount = o.read().decode().strip()
print('Tencent count:', tcount)

# Kill old uvicorn + clean cache
_, o, _ = ssh.exec_command('pkill -9 -f uvicorn; find /opt/marketview -name "*.pyc" -delete 2>/dev/null; find /opt/marketview -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo cleaned')
print(o.read().decode()[:100])

# Restart
time.sleep(3)
_, o, _ = ssh.exec_command('systemctl start marketview; echo ok')
print('restart:', o.read().decode()[:50])
time.sleep(15)

# Wait
print('Waiting 140s for akshare US...')
time.sleep(140)

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/us/spot?limit=3')
r = o.read().decode(errors='replace')
try:
    d = json.loads(r)
    n = len(d.get('data',[]))
    print(f'US spot: {n} items')
    if n:
        print('  first:', d['data'][0].get('名称','?'), d['data'][0].get('最新价','?'))
except:
    print('US spot raw:', r[:100])

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

ssh.close()
