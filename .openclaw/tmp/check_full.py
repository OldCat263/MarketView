# -*- coding: utf-8 -*-
import paramiko, json, sys
PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

# 1. 查 index spot 数据格式
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/index?limit=20'")
raw = o.read().decode(errors='replace')
try:
    d = json.loads(raw)
    if isinstance(d, dict) and 'global' in d:
        print("=== INDEX GLOBAL 前10条 ===")
        for item in d.get('global', [])[:10]:
            code = item.get('代码', '?')
            name = item.get('名称', '?')
            print(f'  code="{code}" name="{name}"')
        print("\n=== INDEX CHINA 前10条 ===")
        for item in d.get('china', [])[:10]:
            code = item.get('代码', '?')
            name = item.get('名称', '?')
            print(f'  code="{code}" name="{name}"')
    else:
        print(f'index format unexpected: {str(d)[:200]}')
except Exception as e:
    print(f'index parse: {e}')
    print(raw[:300])

# 2. 查 US spot
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/us?limit=5'")
raw2 = o.read().decode(errors='replace')
try:
    d2 = json.loads(raw2)
    items = d2.get('data', d2.get('records', []))
    print(f"\n=== US SPOT: {len(items)} 条 ===")
    for item in items[:3]:
        print(f'  {json.dumps(item, ensure_ascii=False)[:150]}')
except Exception as e:
    print(f'us parse: {e}')

# 3. 测试 index K线 - dji
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/index/sh000001?period=1d&count=3'")
print(f"\n=== index Kline sh000001: {o.read().decode(errors='replace')[:100]}")

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/index/dji?period=1d&count=3'")
print(f"=== index Kline dji: {o.read().decode(errors='replace')[:100]}")

# 4. 直接测腾讯 qt.gtimg.cn 美股
_, o, _ = ssh.exec_command("curl -s 'https://qt.gtimg.cn/q=usAAPL' | head -c 200")
print(f"\n=== Tencent US raw: {o.read().decode(errors='replace')[:200]}")

# 5. 试 US KLine
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/us/usAAPL?period=1d&count=5'")
print(f"\n=== US Kline usAAPL: {o.read().decode(errors='replace')[:150]}")

ssh.close()
