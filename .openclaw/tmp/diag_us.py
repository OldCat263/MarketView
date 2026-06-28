import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)

# 测试腾讯 US API
_, o, _ = ssh.exec_command("curl -s 'https://qt.gtimg.cn/q=usAAPL,usMSFT,usGOOGL' 2>&1 | head -5")
print('Tencent US direct:', o.read().decode(errors='replace')[:300])

# 测试 akshare US
_, o, _ = ssh.exec_command("cd /opt/marketview && python3 -c \"import akshare as ak; df=ak.stock_us_spot_em(); print(df.head(2)); print('count:', len(df))\" 2>&1")
print('\nakshare US:', o.read().decode(errors='replace')[:500])

# 查 us roller 最近的错误
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -i '\\[us\\]' | tail -10")
print('\nus roller logs:', o.read().decode(errors='replace')[:500])

ssh.close()
