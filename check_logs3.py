import paramiko, time
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

print(ssh('journalctl -u marketview --no-pager -n 80 --output=cat'))
