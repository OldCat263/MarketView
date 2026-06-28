import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# wait more for roller
time.sleep(30)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
print('US spot:', o.read().decode(errors='replace')[:250])

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep '\\[us\\]' | tail -5")
print('US logs:', o.read().decode(errors='replace')[:300])

ssh.close()
