import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Get full error logs
stdin, stdout, stderr = ssh.exec_command('journalctl -u marketview --no-pager -l --since "5 minutes ago" 2>&1 | grep -i "error\|traceback\|fail\|except" | tail -30', timeout=15)
print('Errors:')
print(stdout.read().decode())

print('\n---')

# Check predict cache key in code
stdin, stdout, stderr = ssh.exec_command('grep -n "cache_key\|rank_" /opt/marketview/backend/main.py | head -20', timeout=10)
print('Cache keys:')
print(stdout.read().decode())

ssh.close()
