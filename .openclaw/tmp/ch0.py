import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# US roller logs
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep '\\[us\\]' | tail -10")
print('US roller:', o.read().decode(errors='replace')[:400])

# US codes
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && /usr/local/bin/python311 -c \"from fetcher.us import _load_us_codes; codes=_load_us_codes(); print('codes:', len(codes)); print('first:', codes[:3])\" 2>&1")
print('\nUS codes:', o.read().decode(errors='replace')[:300])

# Health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('\nHealth:', o.read().decode(errors='replace')[:200])

ssh.close()
