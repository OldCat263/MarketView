import paramiko, time, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# 等 retry 完成（已过了 ~120s 了，retry 最快 75s）
time.sleep(30)

print("=== stock rank ===")
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/rank/stock?period=1d&limit=3')
d = json.loads(o.read().decode())
n = len(d.get('data',[]))
print('items: ' + str(n))
if n > 0:
    print('first: code=' + str(d['data'][0].get('code','?')))

# 查 predict status
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/status/stock')
print('\nstatus stock: ' + o.read().decode(errors='replace')[:100])

# 查 ak stock 预加载进度
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat 2>&1 | tail -10")
out = o.read().decode(errors='replace')
print('\nlast 10 lines:')
for line in out.split('\n')[-5:]:
    if line.strip():
        print(line[:120])
ssh.close()
