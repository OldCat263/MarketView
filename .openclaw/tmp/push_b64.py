import paramiko, json, base64, time

# Prepare: base64 encode the local file
with open(r'D:\服务器ETF\backend\fetcher\us.py', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Write via base64 pipe - guaranteed correct
cmd = f'echo "{b64}" | base64 -d > /opt/marketview/backend/fetcher/us.py'
_, o, _ = ssh.exec_command(cmd)
print('write:', o.read().decode()[:100])

# Verify
_, o, _ = ssh.exec_command("grep -c 'Tencent' /opt/marketview/backend/fetcher/us.py")
tc = o.read().decode().strip()
print('Tencent count:', tc)

_, o, _ = ssh.exec_command("head -40 /opt/marketview/backend/fetcher/us.py")
content = o.read().decode(errors='replace')
for line in content.split('\n')[:40]:
    if 'fetch_shard' in line or 'return' in line or 'def _fetch' in line or 'akshare' in line.lower():
        print('  ', line.strip()[:80])

# Clean pyc + restart
_, o, _ = ssh.exec_command('rm -rf /opt/marketview/backend/__pycache__ /opt/marketview/backend/fetcher/__pycache__; systemctl restart marketview; echo restarted')
print(o.read().decode()[:100])

time.sleep(15)

# Wait 130s
print('Waiting 130s...')
time.sleep(130)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
n = len(d.get('data',[]))
print(f'US spot: {n} items')
if n: print('  first:', d['data'][0].get('名称','?'), d['data'][0].get('最新价','?'))

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health us:', json.loads(o.read().decode())['us'])

ssh.close()
