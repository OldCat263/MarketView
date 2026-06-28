import paramiko

def ssh(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10, allow_agent=False, look_for_keys=False)
    _, o, e = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    c.close()
    return r or '(empty)', err

r, e = ssh('systemctl status marketview 2>&1 | head -20')
print('=== systemctl ===')
print(r)

r2, e2 = ssh('cat /etc/systemd/system/marketview.service 2>&1')
print()
print('=== service file ===')
print(r2[:500])
