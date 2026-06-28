import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Check full logs from last few minutes - unfiltered
stdin, stdout, stderr = ssh.exec_command("journalctl -u marketview --no-pager -o cat --since '3 minutes ago' | tail -80", timeout=15)
print('Recent logs:')
print(stdout.read().decode())

print('\n=== Now check predict status again ===')
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/status/stock?period=1d"', timeout=10)
print('status:', stdout.read().decode())

print('\n=== Trigger with smaller pool to debug ===')
stdin, stdout, stderr = ssh.exec_command('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=10&period=1d"', timeout=30)
print('batch 10:', stdout.read().decode())

import time
time.sleep(30)

stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/status/stock?period=1d"', timeout=10)
print('status after 30s:', stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=10)
print('rank:', stdout.read().decode()[:1000])

ssh.close()
