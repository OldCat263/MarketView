import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Check if falling back appears in logs
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -i 'falling back'")
out = o.read().decode(errors='replace')
print('falling back lines:', out if out.strip() else 'NONE')

# Check all us log lines
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep '\\[us\\]' | tail -15")
print('\nAll US logs post-restart:', o.read().decode(errors='replace')[:600])

# Test _fetch_from_em directly  
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && timeout 30 /usr/local/bin/python311 -c \"from fetcher.us import _fetch_from_em; rows=_fetch_from_em(0,11); print('em rows:',len(rows))\" 2>&1")
print('\nDirect _fetch_from_em:', o.read().decode(errors='replace')[:300])

ssh.close()
