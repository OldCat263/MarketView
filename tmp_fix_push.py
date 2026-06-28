import paramiko, time, json

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

# Step 1: Push scorer.py
print('=== Pushing scorer.py ===')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10, allow_agent=False, look_for_keys=False)
s = c.open_sftp()
s.put(r'D:\服务器ETF\backend\fetcher\scorer.py', '/opt/marketview/backend/fetcher/scorer.py')
s.close()
c.close()
print('PUSH_OK')

# Step 2: Restart
print('=== Restarting marketview ===')
r = ssh_cmd('systemctl restart marketview')
print('RESTART_CMD_OK')

# Step 3: Wait 10s
print('=== Waiting 10s ===')
time.sleep(10)

# Step 4: Check predict status
print('=== Predict status ===')
r = ssh_cmd('curl -s http://localhost:8000/api/predict/status/stock')
print(f'status: {r}')

# Step 5: Predict rank
print('=== Predict rank ===')
r = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5"')
print(f'rank: {r[:500]}')

# Step 6: Health
print('=== Health ===')
r = ssh_cmd('curl -s http://localhost:8000/api/health')
print(f'health: {r[:300]}')

print('DONE')
