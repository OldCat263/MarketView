import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test Tencent output for known vs unknown codes
tests = {'usAAPL': 'known', 'us105.INLF': 'unknown suffix'}
for code, label in tests.items():
    _, o, _ = ssh.exec_command(f'curl -s "https://qt.gtimg.cn/q={code}" 2>&1')
    raw = o.read()
    # Check if has valid data
    text = raw.decode('utf-8', errors='replace')
    has_data = '="' in text and '~~' not in text[:50]
    print(f'{label} {code}: has_data={has_data} len={len(raw)}')

ssh.close()
