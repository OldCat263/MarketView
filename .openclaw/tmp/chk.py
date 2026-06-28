import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -E '\\[us\\]|falling back|akshare' | tail -10")
print(o.read().decode(errors='replace')[:500])

# Check what the deployed us.py looks like
_, o, _ = ssh.exec_command("grep -n 'falling back\\|fetch_from_em\\|stock_us_spot_em' /opt/marketview/backend/fetcher/us.py")
print('\nDeployed code:', o.read().decode(errors='replace')[:300])

ssh.close()
