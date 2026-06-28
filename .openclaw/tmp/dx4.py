import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Try day kline (fqkline) which might work differently
urls = [
    ('dji day', 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=dji,day,,10'),
    ('us.dji day', 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=us.dji,day,,10'),
    ('usDJI day', 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=us.DJI,day,,10'),
]

for label, url in urls:
    _, o, _ = ssh.exec_command(f"curl -s '{url}' 2>&1 | python3 -c \"import sys,json;d=json.load(sys.stdin);print('code',d.get('code'),'has data:',bool(d.get('data')))\" 2>&1")
    print(f'{label}: {o.read().decode(errors="replace")[:150]}')

ssh.close()
