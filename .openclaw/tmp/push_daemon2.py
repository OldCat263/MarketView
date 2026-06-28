import paramiko, json, time

pw = open(r'D:\服务器ETF\.openclaw\tmp\.pw').read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\backend\main.py', '/opt/marketview/backend/main.py')
sftp.close()
print('pushed')
ssh.exec_command('pkill -9 -f uvicorn; sleep 2; systemctl start marketview')
print('restarted')
time.sleep(15)

# Wait 60s for daemon
print('waiting 70s...')
time.sleep(70)

for m in ['stock','etf','hk']:
    _, o, _ = ssh.exec_command(f'curl -s "http://localhost:8000/api/predict/rank/{m}?period=1d&limit=3"')
    d = json.loads(o.read().decode(errors='replace'))
    n = len(d.get('data',[]))
    print(f'{m}: {n} items')
    if n: print('  first:', d['data'][0].get('代码','?'), d['data'][0].get('score','?'))
ssh.close()
