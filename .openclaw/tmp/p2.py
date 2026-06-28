import paramiko, time, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
time.sleep(30)
for m in ('stock','etf','hk'):
    _, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/rank/' + m + '?period=1d&limit=3')
    d = json.loads(o.read().decode())
    n = len(d.get('data',[]))
    print(m + ': ' + str(n) + ' items', end='')
    if n > 0:
        s = d['data'][0]
        print(' | first=' + str(s.get('code','?')) + ' score=' + str(s.get('score',{}).get('total','?')))
    else:
        print()
_, o, _ = ssh.exec_command('journalctl -u marketview --no-pager -n 50 --output=cat')
lines = o.read().decode(errors='replace').split('\n')
for line in lines:
    if 'predict_daemon' in line or 'retry' in line.lower():
        print(line)
ssh.close()
