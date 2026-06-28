import paramiko

PASS = r'Qwe134679'

def ssh(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=*** timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

print('=== PREDICT STATUS ===')
print(ssh('curl -s http://localhost:8000/api/predict/status/stock'))
print()
print('=== RANK ===')
r = ssh('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5"')
print(r[:500] if r else '(empty)')
print()
print('=== HEALTH ===')
print(ssh('curl -s http://localhost:8000/api/health'))
print()
print('=== LAST 50 LINES (key) ===')
logs = ssh('journalctl -u marketview --no-pager -n 200 --output=cat')
for l in logs.splitlines():
    ll = l.lower()
    if 'preload' in ll or 'predict' in ll or 'batch' in ll or 'snapshot' in ll or 'lifespan' in ll or 'roller' in ll:
        print(l[:200])
