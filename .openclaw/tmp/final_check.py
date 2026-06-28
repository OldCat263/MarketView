import paramiko, json, time

pw = open(r'D:\服务器ETF\.openclaw\tmp\.pw').read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# Health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

# DJI kline
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/kline/index/dji?period=1d&count=5"')
k = o.read().decode(errors='replace')
print('\nDJI kline:', k[:300])

# US spot
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
print('US spot:', o.read().decode(errors='replace')[:200])

# Predict etf
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/etf?period=1d&limit=3"')
print('ETF predict:', o.read().decode(errors='replace')[:200])

ssh.close()
