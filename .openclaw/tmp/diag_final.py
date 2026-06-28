import paramiko

with open(r'D:\服务器ETF\.openclaw\tmp\.pw') as f:
    pw = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)

# Recent logs - look for akshare progress / errors
# Check if us loader thread is active
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat --since '4 minutes ago' | grep -v 'Please wait' | head -20")
print(o.read().decode(errors='replace')[:800])

# Check specifically for the akshare em loaded log  
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | grep -E 'akshare em|us.*roller.*start|us.*shard.*err|\_initial' | tail -5")
print('\n--- US key logs ---')
print(o.read().decode(errors='replace')[:500])

# Check systemctl status
_, o, _ = ssh.exec_command('systemctl status marketview --no-pager --lines=5 2>&1')
print('\n--- service status ---')
print(o.read().decode(errors='replace')[:400])

ssh.close()
