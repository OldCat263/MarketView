import paramiko, json
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r
print('=== KLINE sh600519 ===')
print(ssh('curl -s "http://localhost:8000/api/kline/stock/sh600519?period=1d&count=10"')[:300])
print('\n=== KLINE bj920080 ===')
print(ssh('curl -s "http://localhost:8000/api/kline/stock/bj920080?period=1d&count=10"')[:300])
print('\n=== HEALTH ===')
print(ssh('curl -s http://localhost:8000/api/health'))
print('\n=== RANK ===')
print(ssh('curl -s http://localhost:8000/api/predict/rank/stock?period=1d&limit=5')[:300])
