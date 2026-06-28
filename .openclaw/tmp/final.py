import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

print('=== Predict after daemon cycle ===')
time.sleep(5)
for m in ['stock','etf','hk']:
    _, o, _ = ssh.exec_command(f'curl -s "http://localhost:8000/api/predict/rank/{m}?period=1d&limit=3"')
    try:
        d = json.loads(o.read().decode(errors='replace'))
        n = len(d.get('data',[]))
        print(f'  {m}: {n} items')
    except:
        print(f'  {m}: parse error')

print('\n=== US spot ===')
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
print('  us:', o.read().decode(errors='replace')[:150])

print('\n=== DJI K-line ===')
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/kline/index/dji?period=1d&count=3"')
d = json.loads(o.read().decode(errors='replace'))
print(f'  dji: {len(d.get("data",[]))} candles, latest_close={d.get("latest_close")}')

ssh.close()
