import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

urls = [
    ('dji', 'https://ifzq.gtimg.cn/appstock/app/kline/mkline?param=dji,m5,,10'),
    ('us.dji', 'https://ifzq.gtimg.cn/appstock/app/kline/mkline?param=us.dji,m5,,10'),
    ('usdji', 'https://ifzq.gtimg.cn/appstock/app/kline/mkline?param=usdji,m5,,10'),
]

for label, url in urls:
    _, o, _ = ssh.exec_command(f"curl -s '{url}' 2>&1 | python3 -c \"import sys,json;d=json.load(sys.stdin);print('code',d.get('code'),'has data:',bool(d.get('data')))\" 2>&1")
    print(f'{label}: {o.read().decode(errors="replace")[:100]}')

ssh.close()
