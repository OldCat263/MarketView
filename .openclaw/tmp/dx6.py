import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Find venv
_, o, _ = ssh.exec_command('ls /opt/marketview/.venv/bin/python* 2>/dev/null; ls /opt/marketview/backend/.venv/bin/python* 2>/dev/null; which uv 2>/dev/null')
print('python:', o.read().decode(errors='replace')[:300])

# Test akshare with venv
cmd = '/opt/marketview/.venv/bin/python3 -c "import akshare as ak; df=ak.index_us_stock_sina(symbol=\".DJI\"); print(\"rows:\", len(df)); print(df.tail(2))" 2>&1'
_, o, _ = ssh.exec_command(cmd)
print('akshare DJI:', o.read().decode(errors='replace')[:400])

ssh.close()
