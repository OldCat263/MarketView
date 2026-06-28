import paramiko, time, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\backend\main.py', '/opt/marketview/backend/main.py')
sftp.close()
print('SFTP OK')
_, o, _ = ssh.exec_command('systemctl restart marketview')
print('restart OK')
time.sleep(55)
for m in ('stock','etf','hk'):
    _, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/rank/' + m + '?period=1d&limit=3')
    d = json.loads(o.read().decode())
    n = len(d.get('data',[]))
    print(m + ': ' + str(n) + ' items')
    if n > 0:
        s = d['data'][0]
        print('  first: code=' + str(s.get('code','?')) + ' score=' + str(s.get('score',{}).get('total','?')))
_, o, _ = ssh.exec_command('journalctl -u marketview --no-pager -n 30 --output=cat | grep predict_daemon')
print(o.read().decode(errors='replace')[:600])
ssh.close()
