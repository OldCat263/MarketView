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

print('=== Trigger batch predict ===')
r = ssh_cmd('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50"')
print(f'BATCH: {r}')

print('=== Wait 20s ===')
time.sleep(20)

print('=== Predict status ===')
r = ssh_cmd('curl -s http://localhost:8000/api/predict/status/stock')
print(f'status: {r}')

print('=== Predict rank ===')
r = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5"')
try:
    data = json.loads(r)
    items = data.get('data', [])
    print(f'rank: {len(items)} items')
    for item in items[:5]:
        s = item.get('score', {})
        print(f'  {item.get("code","?")}: total={s.get("total_score","?")}')
except:
    print(f'rank_raw: {r[:300]}')

print('DONE')
