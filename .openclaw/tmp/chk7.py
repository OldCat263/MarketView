import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Check if akshare em loaded message ever appeared
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep 'akshare em'")
print('akshare em log:', o.read().decode(errors='replace')[:300] or 'NONE')

# Check us roller errors  
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -E '\\[us\\]' | tail -5")
print('\nus logs:', o.read().decode(errors='replace')[:300])

# Check for any roller errors
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | tail -10")
print('\nrecent:', o.read().decode(errors='replace')[:500])

# Test directly if Python can import us module
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && timeout 60 /usr/local/bin/python311 -c \"from fetcher.us import _fetch_from_em; print('import ok'); rows=_fetch_from_em(0,11); print('shard 0 rows:', len(rows))\" 2>&1")
print('\ndirect test:', o.read().decode(errors='replace')[:500])

ssh.close()
