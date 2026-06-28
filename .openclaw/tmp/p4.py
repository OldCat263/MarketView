import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# 查 daemon 代码确认部署
_, o, _ = ssh.exec_command("grep -n 'time.sleep(45' /opt/marketview/backend/main.py")
print('sleep(45) line:', o.read().decode().strip())

_, o, _ = ssh.exec_command("grep -n 'failed_modules' /opt/marketview/backend/main.py")
print('failed_modules line:', o.read().decode().strip())

# 查 predict daemon 日志
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat 2>&1 | tail -100")
out = o.read().decode(errors='replace')
for line in out.split('\n'):
    if any(w in line.lower() for w in ('predict_daemon','retry','failed','_predict','cache]')):
        print(line)

# predict 磁盘缓存  
_, o, _ = ssh.exec_command("python3 -c \"import json;d=json.load(open('/opt/marketview/backend/.cache/spot_cache.json'));p=d.get('predict',{});print({k:len(v.get('data',[])) for k,v in p.items()})\"")
print('\npredict disk cache:', o.read().decode(errors='replace')[:300])

ssh.close()
