import paramiko
PASS = 'Qwe134679'
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('43.156.133.37', username='root', password=*** timeout=10, allow_agent=False, look_for_keys=False)

def cmd(x):
    _, o, _ = c.exec_command(x)
    return o.read().decode(errors='replace').strip()

print('HEALTH:', cmd('curl -s http://localhost:8000/api/health'))
print()
print('PREDICT STATUS:', cmd('curl -s http://localhost:8000/api/predict/status/stock'))
print()
r = cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5"')
print('RANK full:', r[:800])
print()
print('RANK data length:', len(r))
c.close()
