import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\mcp\marketview_mcp.py', '/opt/marketview/mcp/marketview_mcp.py')
sftp.close()
print('SFTP OK')

_, o, _ = ssh.exec_command('systemctl restart marketview')
print('restart OK')
time.sleep(8)

# version
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/version')
print('version:', o.read().decode(errors='replace')[:200])

# health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('health:', o.read().decode(errors='replace')[:200])

ssh.close()
