import paramiko
pw = "Qwe134679"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)
_, o, _ = ssh.exec_command('systemctl is-active marketview; journalctl -u marketview --no-pager --output=cat -n 15')
print(o.read().decode(errors='replace')[:1500])
ssh.close()
