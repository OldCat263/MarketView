import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat --since '2 min ago' | grep -ivE 'crypto.*_test|Please wait|running _ping'")
print(o.read().decode(errors='replace')[:2000] or '(无其他日志)')
ssh.close()
