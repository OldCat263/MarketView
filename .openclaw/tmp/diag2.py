import paramiko

pw = open(r'D:\服务器ETF\.openclaw\tmp\.pw').read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# Check how health determines us:false
_, o, _ = ssh.exec_command("grep -n 'def.*health\\|us.*false\\|us in cache' /opt/marketview/backend/main.py | head -10")
print('Health check logic:')
print(o.read().decode()[:600])

# Check if us data actually in memory cache
_, o, _ = ssh.exec_command("grep -n 'has_shard_data\\|def.*health\\|_shard_ready' /opt/marketview/backend/main.py | head -10")
print('\nShard check:')
print(o.read().decode()[:500])

ssh.close()
