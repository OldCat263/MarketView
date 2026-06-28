import paramiko
p = open(r'D:\服务器ETF\.openclaw\tmp\.pw','r',encoding='utf-8').read().strip()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=p, timeout=10)
i, o, e = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 50")
print(o.read().decode(errors='replace')[:4000])
ssh.close()
