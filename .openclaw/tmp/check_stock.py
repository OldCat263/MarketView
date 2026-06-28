import paramiko, json
PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

# stock rank 为什么 0 条？检查 spot 缓存里的代码列表
_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/spot/stock?limit=3'")
d = json.loads(o.read().decode())
print(f'stock spot: {len(d.get("data",d.get("records",[])))} items')

_, o, _ = ssh.exec_command("curl -s 'http://localhost:8000/api/predict/status/stock'")
print(f'status: {o.read().decode(errors="replace")}')

# 看看 daemon 完整日志
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 300 --output=cat | grep -A3 'predict_daemon.*stock'")
print(f'\nstock daemon logs:\n{o.read().decode(errors="replace")[:800]}')

ssh.close()
