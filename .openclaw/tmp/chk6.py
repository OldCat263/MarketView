import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

_, o, _ = ssh.exec_command("grep -n 'us_em_lock\\|akshare em loaded\\|threading' /opt/marketview/backend/fetcher/us.py | head -10")
print('deployed:', o.read().decode(errors='replace')[:400])

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -E '\\[us\\]|akshare em' | tail -6")
print('logs:', o.read().decode(errors='replace')[:600])

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/us/spot?limit=3')
print('us spot:', o.read().decode(errors='replace')[:200])

ssh.close()
