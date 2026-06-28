# -*- coding: utf-8 -*-
import paramiko, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

print("=== spot/index ===")
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/index?limit=5'")
print(o.read().decode(errors='replace')[:300])

print("\n=== index Kline dji ===")
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/index/dji?period=1d&count=3'")
print(o.read().decode(errors='replace')[:100])

# 测腾讯全球指数 K线
print("\n=== Tencent fqkline for dji ===")
_, o, _ = ssh.exec_command("curl -s 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=dji,day,,,3,qfq' | head -c 200")
print(o.read().decode(errors='replace')[:200])

# 测 US KLine - AAPL 怎么传的
print("\n=== Kline AAPL (w/ us prefix from frontend) ===")
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/us/AAPL?period=1d&count=5'")
print(o.read().decode(errors='replace')[:200])

print("\n=== Kline usAAPL (direct with prefix) ===")
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/kline/us/usAAPL?period=1d&count=5'")
print(o.read().decode(errors='replace')[:200])

# US spot codes (要前缀吗)
print("\n=== Tencent US spot raw (usAAPL) ===")
_, o, _ = ssh.exec_command("curl -s 'https://qt.gtimg.cn/q=usAAPL' 2>/dev/null | head -c 300")
txt = o.read().decode(errors='replace')
print(txt[:200])

ssh.close()
