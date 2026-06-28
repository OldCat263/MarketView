import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# verify kline.py deployed
_, o, _ = ssh.exec_command("grep -n 'GLOBAL_INDEX_MAP' /opt/marketview/backend/fetcher/kline.py")
print('deployed:', o.read().decode(errors='replace')[:300])

# test dji directly
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && /usr/local/bin/python311 -c \"from fetcher.kline import fetch_kline_index; rows=fetch_kline_index('dji','1d',5); print('dji rows:', len(rows)); print(rows[0] if rows else 'EMPTY')\" 2>&1")
print('direct test:', o.read().decode(errors='replace')[:400])

ssh.close()
