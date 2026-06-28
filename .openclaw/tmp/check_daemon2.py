import paramiko
PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

# check all predict rank
for m in ('stock', 'etf', 'hk'):
    _, o, _ = ssh.exec_command(f"curl -s 'http://localhost:8000/api/predict/rank/{m}?period=1d&limit=3'")
    import json
    try:
        d = json.loads(o.read().decode())
        print(f'{m}: {len(d.get("data",[]))} items')
        if d.get('data'):
            print(json.dumps(d['data'][0], ensure_ascii=False)[:150])
    except:
        print(f'{m}: parse error')

# full daemon section
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 200 --output=cat | awk '/predict_daemon|_percentile|RESTART_OK|_load_cache/' | tail -20")
print(f'\ndetailed logs:\n{o.read().decode(errors="replace")[:1000]}')

ssh.close()
