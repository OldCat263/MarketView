import paramiko, time, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# 等 retry 跑完（已经过了 ~85s，再来可能第二次 retry）
time.sleep(35)

for m in ('stock','etf','hk'):
    _, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/predict/rank/' + m + '?period=1d&limit=3')
    d = json.loads(o.read().decode())
    n = len(d.get('data',[]))
    print(m + ': ' + str(n) + ' items', end='')
    if n > 0:
        print(' | code=' + str(d['data'][0].get('code','?')))
    else:
        print()

# 完整 predict_daemon 日志
_, o, _ = ssh.exec_command('journalctl -u marketview --no-pager -n 80 --output=cat | grep "predict_daemon\|retry\|_initial_load\|stock done"')
out = o.read().decode(errors='replace').strip()
print('\n--- daemon logs ---')
if out:
    print(out)
else:
    print('(empty)')
    # fallback: 全量后续日志
    _, o, _ = ssh.exec_command('journalctl -u marketview --no-pager -n 30 --output=cat')
    print(o.read().decode(errors='replace')[-800:])

ssh.close()
