import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Test what Tencent returns for these codes
tests = 'usAAPL,usMSFT,us105.INLF,us107.SOXS'
_, o, _ = ssh.exec_command(f'curl -s "https://qt.gtimg.cn/q={tests}" 2>&1 | head -5')
out = o.read().decode(errors='replace')
print('Tencent test:')
for line in out.split('\n'):
    line = line.strip()
    if line:
        if '="' in line:
            parts = line.split('="', 1)
            fields = parts[1].rstrip('\";').split('~')
            if len(fields) > 3:
                print(f'  {parts[0]} -> name={fields[1]} price={fields[3]}')
            else:
                print(f'  {parts[0]} -> {len(fields)} fields')
        else:
            print(f'  {line[:80]}')

# Also test without suffix
tests2 = 'us105,us107'
_, o, _ = ssh.exec_command(f'curl -s "https://qt.gtimg.cn/q={tests2}" 2>&1 | head -5')
out2 = o.read().decode(errors='replace')
print('\nWithout suffix:')
for line in out2.split('\n'):
    if line.strip():
        if '="' in line:
            parts = line.split('="', 1)
            fields = parts[1].rstrip('\";').split('~')
            print(f'  {parts[0]} -> {len(fields)} fields')
        else:
            print(f'  {line[:80]}')

ssh.close()
