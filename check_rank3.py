import paramiko, json
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

# 当前 rank
print('=== RANK NOW ===')
print(ssh('curl -s http://localhost:8000/api/predict/rank/stock?period=1d&limit=5'))
print('\n=== PREDICT STATUS ===')
print(ssh('curl -s http://localhost:8000/api/predict/status/stock'))
print('\n=== HEALTH ===')
print(ssh('curl -s http://localhost:8000/api/health'))
print('\n=== LAST 10 LINES ===')
print(ssh('journalctl -u marketview --no-pager -n 10 --output=cat'))
