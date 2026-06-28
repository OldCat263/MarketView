import paramiko, json, time

# Read local file content
with open(r'D:\服务器ETF\backend\fetcher\us.py', 'r', encoding='utf-8') as f:
    local_content = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Use SFTP with explicit truncation
sftp = ssh.open_sftp()
with sftp.open('/opt/marketview/backend/fetcher/us.py', 'w') as f:
    f.write(local_content)
sftp.close()
print('[1] Pushed via write')

# Verify it's correct
_, o, _ = ssh.exec_command("grep -c 'fetch_shard' /opt/marketview/backend/fetcher/us.py")
print('[2] fetch_shard count:', o.read().decode().strip())

_, o, _ = ssh.exec_command("grep 'return _fetch_from_em' /opt/marketview/backend/fetcher/us.py")
print('[3] fetch_shard body:', o.read().decode().strip())

# Clean .pyc
_, o, _ = ssh.exec_command('find /opt/marketview -name "us.cpython*" -delete 2>/dev/null; find /opt/marketview -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo cleaned')
print('[4]', o.read().decode().strip())

# Hard restart
_, o, _ = ssh.exec_command('systemctl stop marketview; sleep 2; systemctl start marketview; echo ok')
print('[5]', o.read().decode().strip())
time.sleep(15)

# Wait 100s for akshare to populate
print('[6] Waiting 100s for akshare...')
time.sleep(100)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
n = len(d.get('data',[]))
print(f'[7] US spot: {n} items')
if n > 0:
    first = d['data'][0]
    print(f'     first: {first.get("名称","?")} ${first.get("最新价","?")}')

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
h = json.loads(o.read().decode(errors='replace'))
print(f'[8] Health us: {h.get("us")}')

ssh.close()
