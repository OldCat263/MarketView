import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Try akshare for global index kline
cmd = "cd /opt/marketview && timeout 30 python3 -c \"import akshare as ak; df=ak.index_us_stock_sina(symbol='.DJI'); print('rows:', len(df)); print(df.tail(3))\" 2>&1"
_, o, _ = ssh.exec_command(cmd)
print('akshare DJI:', o.read().decode(errors='replace')[:400])

ssh.close()
