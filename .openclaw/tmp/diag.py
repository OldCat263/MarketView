import paramiko

pw = open(r'D:\服务器ETF\.openclaw\tmp\.pw').read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat --since '4 minutes ago' | grep -v 'Please wait' | head -15")
print('Recent logs:')
print(o.read().decode(errors='replace')[:800])

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -iE 'akshare em|roller.*us.*start|_initial_load.*us' | tail -5")
print('\nUS key:')
print(o.read().decode(errors='replace')[:500])

ssh.close()
