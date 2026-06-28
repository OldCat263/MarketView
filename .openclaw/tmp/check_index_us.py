import paramiko, json
PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=*** timeout=10)

# 查 index spot 数据里的代码格式
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/index?limit=10'")
try:
    d = json.loads(o.read().decode())
    items = d.get('data', d.get('records', [])) if isinstance(d, dict) else d
    print('=== INDEX SPOT 前10条代码 ===')
    for item in items[:10]:
        code = item.get('代码', '?')
        name = item.get('名称', '?')
        print(f'  code={code}  name={name}')
except:
    print(f'parse error: {o.read().decode(errors="replace")[:300]}')

# 查 US spot
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/us?limit=5'")
try:
    d = json.loads(o.read().decode())
    items = d.get('data', d.get('records', [])) if isinstance(d, dict) else d
    print(f'\n=== US SPOT: {len(items)} 条 ===')
    for item in items[:5]:
        print(f'  {json.dumps(item, ensure_ascii=False)[:120]}')
except:
    print(f'\nus: {o.read().decode(errors="replace")[:200]}')

# 直接测腾讯 US K线
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/us/AAPL?period=1d&count=5'")
print(f'\n=== US K线 AAPL ===')
print(o.read().decode(errors='replace')[:200])

ssh.close()
