import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# check lifespan startup
_, o, _ = ssh.exec_command("grep -n 'predict_daemon\|_save_cache_task\|_load_cache\|Thread.*target' /opt/marketview/backend/main.py | head -10")
print(o.read().decode(errors='replace'))

# check if daemon started
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat 2>&1 | tail -20")
out = o.read().decode(errors='replace')
for line in out.split('\n'):
    if 'RESTART' in line or 'predict' in line.lower() or 'cache' in line.lower() or 'lifespan' in line.lower():
        print('>> '+line)

ssh.close()
