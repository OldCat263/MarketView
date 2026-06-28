import paramiko

def ssh(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10, allow_agent=False, look_for_keys=False)
    _, o, e = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    c.close()
    return r, err

r, e = ssh('grep -n "stock_prefix\\|CODE_PREFIX\\|bj920" /opt/marketview/backend/main.py 2>&1 | head -30')
print('=== hotfix symbols ===')
print(r[:500] if r else '(empty)')
if e: print('ERR:', e)

print()
r2, e2 = ssh('grep -c "_stock_prefix" /opt/marketview/backend/main.py 2>&1')
print('=== _stock_prefix count ===')
print(r2 or '(empty)')

print()
r3, e3 = ssh('cat /opt/marketview/backend/main.py | wc -l')
print('=== line count ===')
print(r3 or '(empty)')

print()
r4, e4 = ssh('head -5 /opt/marketview/backend/main.py')
print('=== first 5 lines ===')
print(r4 or '(empty)')
