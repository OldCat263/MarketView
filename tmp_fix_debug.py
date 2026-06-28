import paramiko

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

def ssh_cmd(cmd):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, e = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

print('=== Debug rank raw ===')
r = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5"')
print(f'rank: {r[:800]}')

print('=== Check server logs ===')
r = ssh_cmd('journalctl -u marketview --no-pager -n 50')
print(f'logs: {r[-1000:]}')

print('DONE')
