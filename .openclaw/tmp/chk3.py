import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Check if akshare _fetch_from_em has populated the cache by now
time.sleep(10)  # akshare stock_us_spot_em is still running (135 batches)
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
d = json.loads(o.read().decode(errors='replace'))
print('US spot items:', len(d.get('data',[])))
if d.get('data'):
    print('  first:', d['data'][0].get('名称','?'), d['data'][0].get('最新价','?'))

# Health - check us flag
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
h = json.loads(o.read().decode(errors='replace'))
print('Health us:', h.get('us'))

# Check if akshare em is done
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | tail -5 | grep -v 'Please wait'")
print('\nRecent logs:', o.read().decode(errors='replace')[:400])

ssh.close()
