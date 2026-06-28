import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)
i, o, e = ssh.exec_command('journalctl -u marketview --no-pager --output=cat -n 30')
print(o.read().decode(errors='replace')[:3000])
ssh.close()
