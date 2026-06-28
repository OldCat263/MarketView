import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Check predict endpoint directly
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10"', timeout=15)
r = stdout.read().decode()
print('Predict rank:', r[:500])

# Check if asyncio is in remote main.py
stdin, stdout, stderr = ssh.exec_command('grep -c "asyncio" /opt/marketview/backend/main.py', timeout=10)
c = stdout.read().decode().strip()
print(f'asyncio lines in remote main.py: {c}')

# Check remote file mod time
stdin, stdout, stderr = ssh.exec_command('ls -la /opt/marketview/backend/main.py', timeout=10)
print('Remote file:', stdout.read().decode().strip())

# Check if there are any errors in uvicorn output for predict
stdin, stdout, stderr = ssh.exec_command('journalctl -u marketview --no-pager -l | grep -i "predict\|error\|traceback" | tail -20', timeout=10)
print('\nLogs predict/error:')
print(stdout.read().decode())

ssh.close()
