import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Find actual venv from systemd service
_, o, _ = ssh.exec_command('cat /etc/systemd/system/marketview.service 2>/dev/null')
print('service:', o.read().decode(errors='replace')[:400])

# Find venv
_, o, _ = ssh.exec_command('find /opt/marketview -name "activate" -type f 2>/dev/null')
print('venv:', o.read().decode(errors='replace')[:400])

ssh.close()
