import paramiko

with open(r'D:\服务器ETF\.openclaw\tmp\.pw', 'r') as f:
    pw = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# Check _load_cache logs
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -i 'load.*cache\|_load_cache\|restore\|from disk' | tail -10")
print('Load cache logs:')
print(o.read().decode(errors='replace')[:500])

# Check if us data is in the spot_cache file
_, o, _ = ssh.exec_command('python3 -c "import json; d=json.load(open(\"/opt/marketview/backend/.cache/spot_cache.json\")); print(\"us in cache:\", \"us\" in d); ud=d.get(\"us\",{}); print(\"us type:\", type(ud).__name__); print(\"us keys:\", list(ud.keys())[:5] if isinstance(ud,dict) else \"not dict\")" 2>&1')
print('\nUS in spot cache:')
print(o.read().decode(errors='replace')[:400])

# index in spot cache
_, o, _ = ssh.exec_command('python3 -c "import json; d=json.load(open(\"/opt/marketview/backend/.cache/spot_cache.json\")); print(\"index in cache:\", \"index\" in d); idata=d.get(\"index\",{}); print(\"index type:\", type(idata).__name__); print(\"index shard count:\", len(idata.get(\"shards\",{})))" 2>&1')
print('\nIndex in spot cache:')
print(o.read().decode(errors='replace')[:300])

ssh.close()
