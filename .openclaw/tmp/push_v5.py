import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Aggressive pyc cleanup
cmds = [
    'find /opt/marketview -name "*.pyc" -delete 2>/dev/null; echo "pyc done"',
    'find /opt/marketview -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; echo "cache done"',
    'rm -rf /root/.cache/marketview* 2>/dev/null; echo "root clean"',
    'cd /opt/marketview/backend && python3 -B -c "from fetcher.us import fetch_shard; print(\"new import ok\")" 2>&1; echo "direct ok"'
]
for cmd in cmds:
    _, o, _ = ssh.exec_command(cmd)
    print(o.read().decode(errors='replace').strip()[:100])

# Write file again to be sure
with open(r'D:\服务器ETF\backend\fetcher\us.py', 'r', encoding='utf-8') as f:
    local = f.read()

sftp = ssh.open_sftp()
with sftp.open('/opt/marketview/backend/fetcher/us.py', 'w') as f:
    f.write(local)
sftp.close()

# Verify deployed content is ours (Tencent empty should NOT appear)
_, o, _ = ssh.exec_command("grep 'Tencent' /opt/marketview/backend/fetcher/us.py")
result = o.read().decode(errors='replace')
print(f'Tencent check: {"STILL OLD CODE!!!" if "Tencent" in result else "CLEAN ✅"}')

# Kill and restart
_, o, _ = ssh.exec_command('systemctl stop marketview; sleep 3; PYTHONDONTWRITEBYTECODE=1 systemctl start marketview; echo "restarted with nocache"')
print(o.read().decode(errors='replace').strip())

time.sleep(15)

# Check logs immediately
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat --since '30 seconds ago' | grep -E '\\[us\\]|roller.*us' | head -5")
print('fresh logs:', o.read().decode(errors='replace')[:300] or 'no us logs yet')

# Wait for akshare
print('Waiting 120s...')
time.sleep(120)

_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
print(f'US spot: {len(d.get("data",[]))} items')

_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('Health:', o.read().decode(errors='replace')[:200])

ssh.close()
