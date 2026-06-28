import paramiko, re
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 60")
raw = o.read().decode(errors='replace')
# Show non-progress-bar lines
lines = [l for l in raw.split('\n') if l.strip() and 'Please wait' not in l and 'running _ping' not in l and 'crypto.*_test err' not in l and 'Crypto _test' not in l]
print('\n'.join(lines[-25:]))
ssh.close()
