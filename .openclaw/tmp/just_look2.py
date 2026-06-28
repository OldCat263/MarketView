import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 45 | grep -vE 'crypto.*_test err|Please wait|running _ping|^\['")
out = o.read().decode(errors='replace')[:2000]
print(out if out.strip() else '(只有 akshare 进度条，无其他日志)')
ssh.close()
