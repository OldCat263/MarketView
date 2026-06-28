import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# Check if the first shard's akshare call completed
_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager --output=cat | tail -20")
out = o.read().decode(errors='replace')
for line in out.split('\n')[-8:]:
    if line.strip():
        print(line[:120])

# Check if us cache has any data
_, o, _ = ssh.exec_command('curl -s "http://localhost:8000/api/us/spot?limit=3" 2>&1')
print('\nUS spot now:', o.read().decode(errors='replace')[:200])

ssh.close()
