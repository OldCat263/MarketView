import paramiko, json
PASS = 'Qwe134679'
def ssh(cmd):
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('43.156.133.37', username='root', password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
    _, o, _ = c.exec_command(cmd)
    r = o.read().decode(errors='replace').strip()
    c.close()
    return r

# Full logs since last restart
print('=== FULL LOGS (last 200 lines, filter key) ===')
raw = ssh('journalctl -u marketview --no-pager -n 200 --output=cat')
for line in raw.splitlines():
    ll = line.lower()
    if 'code' in ll or 'preload' in ll or 'predict' in ll or 'batch' in ll or 'stock_prefix' in ll or 'roller' in ll or 'lifespan' in ll:
        print(line)
