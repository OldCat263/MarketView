import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10, allow_agent=False, look_for_keys=False)
stdin, stdout, stderr = c.exec_command("journalctl -u marketview --no-pager -n 300 --output=cat | grep -iE 'preload|predict|batch|snapshot|lifespan|roller'")
print(stdout.read().decode(errors='replace'))
c.close()
