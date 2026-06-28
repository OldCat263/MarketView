import paramiko
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd); r = o.read().decode(errors='replace').strip(); c.close(); return r

print('=== _stock_prefix ===')
print(ssh('grep -n "_stock_prefix" /root/marketview/backend/main.py')[:300])
print()
print('=== _CODE_PREFIX ===')
print(ssh('grep -n "_CODE_PREFIX" /root/marketview/backend/main.py')[:300])
print()
print('=== HEALTH ===')
print(ssh('curl -s http://localhost:8000/api/health'))
