import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Try ETF predict (which had a clear error we can fix)
print('=== Try ETF predict ===')
stdin, stdout, stderr = ssh.exec_command('curl -s -X POST "http://localhost:8000/api/predict/batch/etf?pool_size=10&period=1d"', timeout=30)
print('batch etf:', stdout.read().decode())
time.sleep(30)
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/status/etf?period=1d"', timeout=10)
print('etf status:', stdout.read().decode())
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/etf?period=1d&limit=10"', timeout=10)
print('etf rank:', stdout.read().decode()[:1000])

# Also try HK
print('\n=== Try HK predict ===')
stdin, stdout, stderr = ssh.exec_command('curl -s -X POST "http://localhost:8000/api/predict/batch/hk?pool_size=10&period=1d"', timeout=30)
print('batch hk:', stdout.read().decode())
time.sleep(30)
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/hk?period=1d&limit=10"', timeout=10)
print('hk rank:', stdout.read().decode()[:1000])

# Check what rank_batch does - is scorer functional?
print('\n=== Check scorer import ===')
stdin, stdout, stderr = ssh.exec_command('grep -n "scorer\|Scorer\|ranker" /opt/marketview/backend/main.py | head -20', timeout=10)
print(stdout.read().decode())

# Check if rank_batch crashes silently
print('\n=== Check error logs for rank_batch ===')
stdin, stdout, stderr = ssh.exec_command("journalctl -u marketview --no-pager -o cat --since '2 minutes ago' | grep -E 'rank_batch|scorer|error.*batch|0 ranked|int.*get' | tail -20", timeout=10)
print(stdout.read().decode())

ssh.close()
