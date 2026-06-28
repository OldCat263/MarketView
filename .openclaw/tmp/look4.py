import paramiko, re
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 80")
raw = o.read().decode(errors='replace')
# Keep all lines including progress bars
lines = [l for l in raw.split('\n') if l.strip() and 'running _ping' not in l]
print('\n'.join(lines[-30:]))
ssh.close()
