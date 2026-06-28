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

# Check logs for predict progress
print('=== Recent logs ===')
out, err = ssh_cmd('journalctl -u marketview --since "2 minutes ago" --no-pager -l | tail -60')
print(out[-3000:])

print('\n=== Trigger batch and wait longer ===')
out, err = ssh_cmd('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50"', timeout=60)
print(f'batch: {out}')

# Wait 45s total
for attempt in range(3):
    time.sleep(15)
    out, err = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=30)
    rank = json.loads(out)
    items = rank.get('data', [])
    print(f'  [{attempt+1}/3] items={len(items)} cached_at={rank.get("cached_at")}')
    if items:
        break

if not items:
    print('\nTrying without period filter...')
    out, err = ssh_cmd('curl -s "http://localhost:8000/api/predict/rank/stock?limit=10"', timeout=30)
    print(f'no-period: {out[:500]}')

    # Try with mock/backup approach - just get spot data and fake the ranking
    print('\n=== Falling back to spot data ===')
    out, err = ssh_cmd('curl -s "http://localhost:8000/api/spot/stock?limit=50"', timeout=60)
    print(f'spot: {out[:2000]}')
