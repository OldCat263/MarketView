import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Try the batch with larger pool and watch progress
print('[Step 4] Trigger predict batch with pool_size=50...')
stdin, stdout, stderr = ssh.exec_command('curl -s -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50&period=1d"', timeout=30)
print('batch:', stdout.read().decode())

# Poll progress
for attempt in range(12):
    time.sleep(10)
    stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/status/stock?period=1d"', timeout=10)
    status = stdout.read().decode()
    print(f'  [{attempt+1}/12] status={status}')
    try:
        s = json.loads(status)
        if s.get('status') == 'done':
            print('Done! Fetching rank...')
            stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=10)
            rank = stdout.read().decode()
            print(f'rank: {rank[:1000]}')
            r = json.loads(rank)
            items = r.get('data', [])
            if items:
                break
    except:
        pass

print('\n=== Final state ===')
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=10)
final_rank = stdout.read().decode()
stdin2, stdout2, stderr2 = ssh.exec_command('curl -s http://localhost:8000/api/health', timeout=10)
health = stdout2.read().decode()
print(f'Rank: {final_rank[:500]}')
print(f'Health: {health}')

ssh.close()
