import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/kline/index/dji?period=1d&count=10"')
d = json.loads(o.read().decode(errors='replace'))
print('dj k-line candles:', len(d.get('data', [])))
if d.get('data'):
    print('first:', d['data'][0][:4])

ssh.close()
