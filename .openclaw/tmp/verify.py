import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)

# Check what fetch_shard looks like
_, o, _ = ssh.exec_command("sed -n '36,38p' /opt/marketview/backend/fetcher/us.py")
print('us.py fetch_shard:', o.read().decode().strip())

# Check kline.py fetch_kline_index  
_, o, _ = ssh.exec_command("grep -A3 'def fetch_kline_index' /opt/marketview/backend/fetcher/kline.py")
print('kline.py index:', o.read().decode().strip())

# Force kill all python, clean all pycache, restart
_, o, _ = ssh.exec_command("pkill -9 -f uvicorn; sleep 2; find /opt/marketview -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find /opt/marketview -name '*.pyc' -delete 2>/dev/null; echo 'cleaned all'; systemctl restart marketview; echo 'restarted'")
print(o.read().decode().strip())

ssh.close()
