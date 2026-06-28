import paramiko, json, time

with open(r'D:\服务器ETF\.openclaw\tmp\.pw', 'r') as f:
    pw = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)

# Check us.py on server
_, o, _ = ssh.exec_command("grep -n 'fetch_shard\\|fetch_from_em\\|threading.Lock' /opt/marketview/backend/fetcher/us.py")
print('Server us.py:')
print(o.read().decode())

# Check kline.py on server
_, o, _ = ssh.exec_command("grep -n 'fetch_kline_index\\|GLOBAL_INDEX_MAP\\|index_us_stock_sina' /opt/marketview/backend/fetcher/kline.py")
print('\nServer kline.py:')
print(o.read().decode())

# Check main.py
_, o, _ = ssh.exec_command("grep -n '_FETCH_FN\\|predict_daemon.*done:' /opt/marketview/backend/main.py | head -5")
print('\nServer main.py:')
print(o.read().decode())

# Clean .pyc and restart
_, o, _ = ssh.exec_command("find /opt/marketview -name '*.pyc' -delete 2>/dev/null; find /opt/marketview -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; systemctl restart marketview; echo ok")
print('\nRestart:', o.read().decode().strip())

ssh.close()
