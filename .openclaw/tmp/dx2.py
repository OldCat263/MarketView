import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

cmd = 'cd /opt/marketview/backend && timeout 60 python3 -c "from fetcher.stock import get_json; import json; d=json.loads(get_json()); print(\"type\", type(d).__name__, \"len\", len(d) if isinstance(d,list) else \"dict\"); print(json.dumps(d[0] if isinstance(d,list) and d else {}, ensure_ascii=False)[:200])" 2>&1'
_, o, _ = ssh.exec_command(cmd)
print('stock fetcher:', o.read().decode(errors='replace')[:400])

# Also check daemon log more carefully
_, o, _ = ssh.exec_command('journalctl -u marketview --no-pager --output=cat | grep -E "stock done: 0|stock error|stock fetch|stock no codes" | tail -5')
print('\nstock errors:', o.read().decode(errors='replace')[:300])

ssh.close()
