import paramiko

def ssh(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

r1 = ssh("curl -s 'http://localhost:8000/api/kline/stock/bj920080?period=1d&count=10' | python3 -m json.tool 2>/dev/null | head -15")
print('=== KLINE bj920080 (北交所) ===')
print(r1)

r2 = ssh("curl -s 'http://localhost:8000/api/kline/stock/sh600519?period=1d&count=5' | python3 -m json.tool 2>/dev/null | head -10")
print()
print('=== KLINE sh600519 (上交所) ===')
print(r2)
