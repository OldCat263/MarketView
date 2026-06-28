import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\backend\fetcher\us.py', '/opt/marketview/backend/fetcher/us.py')
sftp.close()
print('[1/2] us.py pushed')

_, o, _ = ssh.exec_command('systemctl restart marketview')
print('[2/2] restart OK')
time.sleep(15)

# Wait for us roller (needs akshare 135 batches)
print('Waiting 60s for akshare em...')
time.sleep(60)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
n = len(d.get('data',[]))
print(f'US spot: {n} items')
if n > 0:
    first = d['data'][0]
    print(f'  first: {first.get("名称","?")} ${first.get("最新价","?")}')

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
h = json.loads(o.read().decode(errors='replace'))
print(f'Health us: {h.get("us")}')

ssh.close()
