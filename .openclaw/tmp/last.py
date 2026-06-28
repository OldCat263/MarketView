import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Push again
sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\backend\fetcher\us.py', '/opt/marketview/backend/fetcher/us.py')
sftp.close()
print('SFTP ok')

# Force kill uvicorn, clean pycache, restart
ssh.exec_command('pkill -9 -f "uvicorn main" 2>/dev/null; sleep 1; echo killed')
time.sleep(2)
ssh.exec_command('rm -rf /opt/marketview/backend/__pycache__ 2>/dev/null; echo cache-gone')
ssh.exec_command('systemctl restart marketview; echo restarted')
time.sleep(3)

# Check file
_, o, _ = ssh.exec_command("grep -c 'Tencent' /opt/marketview/backend/fetcher/us.py")
print('Tencent count:', o.read().decode().strip())

# Check akshare em loaded log
_, o, _ = ssh.exec_command("journalctl -u marketview --since '10 seconds ago' --no-pager | grep 'akshare em' 2>/dev/null || echo NONE")
print('loaded:', o.read().decode().strip()[:100])

time.sleep(200)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
print('US spot:', len(d.get('data',[])), 'items')
ssh.close()
