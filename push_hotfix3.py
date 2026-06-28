import paramiko, json, time

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

def ssh_cmd(cmd, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ssh.close()
    return out, err

print('[Step 3 retry] Waiting for modules (etf, us, crypto still false)...')
for attempt in range(10):
    time.sleep(10)
    out, err = ssh_cmd('curl -s http://localhost:8000/api/health')
    h = json.loads(out)
    stock=h.get('stock'); etf=h.get('etf'); hk=h.get('hk'); us=h.get('us'); idx=h.get('index'); crypto=h.get('crypto'); predict=h.get('predict')
    ready = sum(1 for x in [stock, etf, hk, us, idx] if x)
    print(f'  [{attempt+1}] stock={stock} etf={etf} hk={hk} us={us} index={idx} predict={predict} ready={ready}/5')
    if ready >= 4:
        print('[Step 3] Modules sufficiently ready!')
        break

print('\n[Step 4] Trigger predict batch...')
out, err = ssh_cmd('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50"', timeout=60)
print(f'  batch: {out}')

print('\n[Step 5] Waiting 30s for computation...')
time.sleep(30)

print('Querying rank...')
out, err = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=30)
rank = json.loads(out)
items = rank.get('data', [])
print(f'  rank items: {len(items)}')

if items:
    for i, item in enumerate(items[:10]):
        code = item.get('code', item.get('symbol', '?'))
        score = item.get('score', item.get('total_score', '?'))
        name = item.get('name', '')
        print(f'  {i+1}. {code} {name}: {score}')
else:
    print('  No items in rank. Full response:')
    print(f'  {out[:1000]}')

# Final health
print('\n=== FINAL REPORT ===')
out, err = ssh_cmd('curl -s http://localhost:8000/api/health')
h = json.loads(out)
print(f'Health: stock={h.get("stock")} etf={h.get("etf")} hk={h.get("hk")} us={h.get("us")} index={h.get("index")} crypto={h.get("crypto")}')
print(f'Rank stock(1d): {len(items)} items')
if items:
    print('Top 5:')
    for i, item in enumerate(items[:5]):
        code = item.get('code', item.get('symbol', '?'))
        score = item.get('score', item.get('total_score', '?'))
        name = item.get('name', '')
        print(f'  {i+1}. {code} {name}: {score}')
