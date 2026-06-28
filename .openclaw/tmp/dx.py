import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test Tencent US direct
cmd1 = 'curl -s "https://qt.gtimg.cn/q=usAAPL,usMSFT" 2>&1 | head -4'
_, o, _ = ssh.exec_command(cmd1)
b = o.read()
print('Tencent US bytes:' + str(len(b)) + ' -> ' + repr(b[:200]))

# Test akshare US
cmd2 = 'cd /opt/marketview && timeout 30 python3 -c "import akshare as ak; df=ak.stock_us_spot_em(); print(\"rows:\", len(df)); print(df.head(1))" 2>&1'
_, o, _ = ssh.exec_command(cmd2)
b2 = o.read()
print('\nakshare US bytes:' + str(len(b2)) + ' -> ' + repr(b2[:400]))

ssh.close()
