import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=15)

# Check the batch endpoint code around line 420-470
stdin, stdout, stderr = ssh.exec_command("sed -n '415,475p' /opt/marketview/backend/main.py", timeout=10)
print('Batch endpoint code:')
print(stdout.read().decode())

print('\n---')

# Check all recent logs for predict
stdin, stdout, stderr = ssh.exec_command("journalctl -u marketview --no-pager --since '10 minutes ago' -o cat | grep -i predict | tail -20", timeout=10)
print('Predict logs:')
print(stdout.read().decode())

# Check predict status
print('\n---')
stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/predict/status/stock?period=1d"', timeout=10)
print('Predict status:', stdout.read().decode())

ssh.close()
