import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# 查版本端点
cmd = "grep -n 'version' /opt/marketview/backend/main.py | head -10"
_, o, _ = ssh.exec_command(cmd)
print(o.read().decode(errors='replace'))

# 查所有路由
cmd2 = "grep -n '@app' /opt/marketview/backend/main.py | head -30"
_, o, _ = ssh.exec_command(cmd2)
print(o.read().decode(errors='replace')[:800])

# 直接版本检查
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('health:', o.read().decode(errors='replace')[:300])

ssh.close()
