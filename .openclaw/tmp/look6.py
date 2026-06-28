import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 20 | grep -vE 'running _ping'")
print(o.read().decode(errors='replace')[:2000])
ssh.close()
