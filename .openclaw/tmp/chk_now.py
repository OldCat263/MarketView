import paramiko
pw = open(r'D:\服务器ETF\.openclaw\tmp\.pw').read().strip()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# DJI kline log
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -iE 'kline_index|fetch_kline|global.*index|index_us_stock' | tail -5")
print('Kline logs:')
print(o.read().decode(errors='replace')[:500] or 'NONE')

# US spot direct
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3"')
print('\nUS spot API:', o.read().decode(errors='replace')[:300])

# DJI kline direct
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/kline/index/dji?period=1d&count=3"')
print('\nDJI kline API:', o.read().decode(errors='replace')[:300])

ssh.close()
