import paramiko, time, json, sys

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

local_file = r'D:\服务器ETF\backend\main.py'
remote_path = '/opt/marketview/backend/main.py'

print('[Step 1] Pushing main.py...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

sftp = ssh.open_sftp()
sftp.put(local_file, remote_path)
sftp.close()
print('[Step 1] main.py pushed OK')

print('[Step 2] Restarting marketview...')
stdin, stdout, stderr = ssh.exec_command('systemctl restart marketview', timeout=30)
stdout.read(); stderr.read()
time.sleep(3)
print('[Step 2] Restart triggered')
ssh.close()

print('[Step 3] Waiting for modules ready (max 60s)...')
ready = False
for attempt in range(6):
    time.sleep(10)
    try:
        ssh2 = paramiko.SSHClient()
        ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh2.connect(HOST, username=USER, password=PASS, timeout=15)
        stdin, stdout, stderr = ssh2.exec_command('curl -s http://localhost:8000/api/health', timeout=10)
        out = stdout.read().decode()
        ssh2.close()
        h = json.loads(out)
        mods = h.get('modules', {})
        ok = sum(1 for m in ['stock','etf','hk','us','index'] if mods.get(m) == True)
        print(f'  [{attempt+1}/6] ready={ok}/5  modules={mods}')
        if ok >= 5:
            print('[Step 3] All 5 modules ready!')
            ready = True
            break
    except Exception as e:
        print(f'  [{attempt+1}/6] error: {e}')
if not ready:
    print('[Step 3] WARNING: Not all modules ready, proceeding anyway')

print('[Step 4] Triggering predict batch...')
ssh3 = paramiko.SSHClient()
ssh3.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh3.connect(HOST, username=USER, password=PASS, timeout=15)
url4 = 'http://localhost:8000/api/predict/batch/stock?pool_size=50'
stdin, stdout, stderr = ssh3.exec_command(f'curl -s -X POST "{url4}"', timeout=60)
out4 = stdout.read().decode()
err4 = stderr.read().decode()
print(f'  stdout: {out4[:500]}')
if err4:
    print(f'  stderr: {err4[:200]}')

print('[Step 5] Waiting 15s then querying rank...')
time.sleep(15)
url5 = 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=10'
stdin, stdout, stderr = ssh3.exec_command(f'curl -s "{url5}"', timeout=30)
out5 = stdout.read().decode()
err5 = stderr.read().decode()
ssh3.close()

print('=== RANK DATA ===')
print(out5[:3000])
if err5:
    print('STDERR:', err5[:300])

# Parse rank data
rank_data = json.loads(out5) if out5.strip() else {}
items = rank_data.get('data', rank_data.get('items', []))
print(f'\nRank items count: {len(items)}')

top5 = []
for item in items[:5]:
    code = item.get('code', item.get('symbol', '?'))
    score = item.get('score', item.get('total_score', '?'))
    top5.append((code, score))

print('[Step 6] Final health check...')
ssh4 = paramiko.SSHClient()
ssh4.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh4.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = ssh4.exec_command('curl -s http://localhost:8000/api/health', timeout=10)
health_out = stdout.read().decode()
ssh4.close()

health_json = json.loads(health_out) if health_out.strip() else {}
mods = health_json.get('modules', {})
print(f'Health modules: {mods}')

print('\n=== REPORT ===')
print(f'Health: stock={mods.get("stock")}, etf={mods.get("etf")}, hk={mods.get("hk")}, us={mods.get("us")}, index={mods.get("index")}, crypto={mods.get("crypto")}')
print(f'Rank stock(1d): {len(items)} items')
print('Top 5:')
for code, score in top5:
    print(f'  {code}: {score}')
