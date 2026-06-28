import paramiko, time

PASS = 'Qwe134679'
host = '43.156.133.37'
local = r'D:\服务器ETF\backend\main.py'
remote = '/opt/marketview/backend/main.py'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=*** timeout=10)

sftp = ssh.open_sftp()
sftp.put(local, remote)
sftp.close()
print('SFTP OK ✅')

_, o, _ = ssh.exec_command('systemctl restart marketview')
err = o.read().decode().strip()
print(f'restart: {err or "OK"} ✅')

time.sleep(50)  # 等新 daemon 45s 延迟 + 计算

print('\n=== 验收 ===')
for m in ('stock', 'etf', 'hk'):
    _, o, _ = ssh.exec_command(f"curl -s 'http://localhost:8000/api/predict/rank/{m}?period=1d&limit=3'")
    import json
    try:
        d = json.loads(o.read().decode())
        print(f'{m}: {len(d.get("data",[]))} items')
        if d.get('data'):
            item = d['data'][0]
            print(f'  first: {item.get("code","?")} name={item.get("name","?")[:10]} score={item.get("score",{}).get("total","?")}')
    except Exception as e:
        print(f'{m}: parse error - {e}')

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 30 --output=cat | grep 'predict_daemon'")
print(f'\n{ssh.read().decode(errors="replace")[:600]}')

ssh.close()
