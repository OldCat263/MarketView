import paramiko, json, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# BUG8: 查 us roller 日志
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep '\\[us\\]' | tail -15")
print('=== US roller logs ===')
print(o.read().decode(errors='replace')[:600])

# BUG8: 直接测试 us 的 get_json()
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && /usr/local/bin/python311 -c \"from fetcher.us import get_json, _load_us_codes; codes=_load_us_codes(); print('codes count:',len(codes)); print('first 3:',codes[:3]); import json; d=json.loads(get_json()); print('rows:',len(d))\" 2>&1")
print('\n=== US get_json ===')
print(o.read().decode(errors='replace')[:500])

# BUG10: 测试 daemon 中 get_stock_json 到底返回什么
_, o, _ = ssh.exec_command("cd /opt/marketview/backend && timeout 30 /usr/local/bin/python311 -c \"from fetcher.stock import get_json; import json; s=get_json(); d=json.loads(s); print('type:',type(d).__name__); print('len:',len(d) if isinstance(d,list) else 'dict'); r=d[0] if d else {}; print('first keys:',list(r.keys())[:5] if isinstance(r,dict) else '?'); print('first:',json.dumps(r,ensure_ascii=False)[:200] if d else 'EMPTY')\" 2>&1")
print('\n=== Stock get_json ===')
print(o.read().decode(errors='replace')[:400])

ssh.close()
