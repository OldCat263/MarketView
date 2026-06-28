import paramiko, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# 查服务器 main.py L270-275
_, o, _ = ssh.exec_command("sed -n '268,276p' /opt/marketview/backend/main.py")
print("Server lines 268-276:")
print(o.read().decode(errors='replace'))

# 等 retry 可能完成
time.sleep(45)

import json
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/rank/stock?period=1d&limit=3')
d = json.loads(o.read().decode())
print('\nstock rank: ' + str(len(d.get('data',[]))) + ' items')
if d.get('data'):
    print('first code=' + str(d['data'][0].get('code','?')))

ssh.close()
