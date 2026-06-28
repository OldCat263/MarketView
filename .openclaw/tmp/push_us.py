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

# Health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

# US spot - wait a bit for roller
time.sleep(20)
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
print('US spot:', o.read().decode(errors='replace')[:200])

ssh.close()
