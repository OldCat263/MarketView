import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test: strip suffix after dot
tests = [
    ('AAPL', 'usAAPL'),
    ('105.INLF', 'us105'),  # strip .INLF
    ('107.SOXS', 'us107'),  # strip .SOXS
    ('105.GDC', 'us105'),   # strip .GDC
]

for raw_code, us_code in tests:
    _, o, _ = ssh.exec_command(f'curl -s "https://qt.gtimg.cn/q={us_code}" 2>&1')
    data = o.read()
    has = '="' in data.decode('utf-8', errors='replace') and len(data) > 80
    print(f'{raw_code} -> {us_code}: data={has} ({len(data)} bytes)')

ssh.close()
