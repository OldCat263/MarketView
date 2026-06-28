import paramiko, time

PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

# 等 daemon 跑完（30s 延迟 + 计算）
print('等待 predict daemon 首次计算...')
time.sleep(30)

print('--- verify daemon ---')
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(f'predict status: {o.read().decode(errors="replace")[:100]}')

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=5'")
import json
try:
    d = json.loads(o.read().decode())
    print(f'predict rank: {len(d.get("data",[]))} items')
    if d.get('data'):
        print(json.dumps(d['data'][0], indent=2)[:300])
except:
    print('rank parse error')

# 查 daemon 日志
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 50 --output=cat | grep 'predict_daemon'")
print(f'daemon logs: {o.read().decode(errors="replace")[:500]}')

# 查 _percentile_rank 相关错误
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 100 --output=cat | grep -i 'percentile\\|error\\|traceback\\|attributeerror' | tail -5")
print(f'errors: {o.read().decode(errors="replace")[:300]}')

ssh.close()
