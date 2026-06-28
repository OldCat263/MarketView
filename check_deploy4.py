import paramiko
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, e = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    c.close()
    return (r, err)

r, e = ssh('find /root/marketview -name main.py 2>/dev/null')
print('=== find main.py ===')
print(r or '(empty)')
if e: print('ERR:', e)

print()
r2, e2 = ssh('ls -la /root/marketview/backend/ 2>&1')
print('=== backend dir ===')
print(r2 or '(empty)')
if e2: print('ERR:', e2)

print()
r3, e3 = ssh('cat /root/marketview/Procfile 2>/dev/null; systemctl list-units --type=service --state=running | grep market 2>&1')
print('=== procfile/systemd ===')
print(r3 or '(empty)')
