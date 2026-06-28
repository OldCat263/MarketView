import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test with system python311
cmd = '/usr/local/bin/python311 -c "import akshare as ak; df=ak.index_us_stock_sina(symbol=\\\".DJI\\\"); print(\\\"rows:\\\", len(df)); print(df.tail(2))" 2>&1'
_, o, _ = ssh.exec_command(cmd)
out = o.read().decode(errors='replace')
print('akshare DJI:', out[:400])

# Also check if httpx is available
_, o, _ = ssh.exec_command('/usr/local/bin/python311 -c "import httpx; print(\"httpx OK\")" 2>&1')
print('httpx:', o.read().decode(errors='replace')[:100])

# Check error more carefully
if 'ModuleNotFoundError' in out:
    _, o, _ = ssh.exec_command('/usr/local/bin/python311 -m pip list 2>&1 | grep -i akshare')
    print('akshare pip:', o.read().decode(errors='replace')[:200])

ssh.close()
