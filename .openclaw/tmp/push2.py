import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\backend\fetcher\us.py', '/opt/marketview/backend/fetcher/us.py')
sftp.close()

_, o, _ = ssh.exec_command('systemctl restart marketview')
time.sleep(15)

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

# wait for us roller
time.sleep(30)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
print('US spot items:', len(d.get('data',[])))
if d.get('data'):
    print('  first:', d['data'][0].get('名称','?'), d['data'][0].get('最新价','?'))
else:
    print('  STILL EMPTY')

ssh.close()
