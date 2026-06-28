import paramiko
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd); r = o.read().decode(errors='replace').strip(); c.close(); return r

# Full file existence check
print('=== main.py path ===')
print(ssh('ls -la /root/marketview/backend/main.py'))
print()
print('=== grep -n def stock ===')
print(ssh("grep -n 'def stock\\|CODE_PREFIX\\|stock_prefix' /root/marketview/backend/main.py")[:500])
print()
print('=== grep bj prefix ===')
print(ssh("grep -n 'bj\\|sh\\|sz' /root/marketview/backend/main.py | head -20"))
