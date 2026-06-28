import paramiko, json

with open(r'D:\服务器ETF\.openclaw\tmp\.pw', 'r') as f:
    pw = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# Check disk cache status - does it have data?
_, o, _ = ssh.exec_command('python3 -c "import json,os; p=\"/opt/marketview/backend/.cache/spot_cache.json\"; d=json.load(open(p)); print(\"spot_cache keys:\", list(d.keys())); print(\"sizes:\", {k: len(str(v)) for k,v in d.items() if k != \"predict\"})\" 2>&1')
print('Spot cache:')
print(o.read().decode(errors='replace')[:500])

# Check kline cache
_, o, _ = ssh.exec_command('python3 -c "import json,os; p=\"/opt/marketview/backend/.cache/kline_cache.json\"; print(\"exists:\", os.path.exists(p)); d=json.load(open(p)) if os.path.exists(p) else {}; print(\"keys:\", list(d.keys())[:5])\" 2>&1')
print('\nKline cache:')
print(o.read().decode(errors='replace')[:300])

# Check file sizes
_, o, _ = ssh.exec_command('ls -la /opt/marketview/backend/.cache/ 2>&1')
print('\nCache dir:')
print(o.read().decode(errors='replace')[:400])

ssh.close()
