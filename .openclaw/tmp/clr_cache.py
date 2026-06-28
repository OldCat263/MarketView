import paramiko, time, base64
pw = base64.b64decode(b'UXdlMTM0Njc5').decode()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)
# Delete old cache files
ssh.exec_command('rm -f /opt/marketview/backend/.cache/spot_cache.json /opt/marketview/backend/.cache/kline_cache.json && echo deleted')
time.sleep(1)
# Restart to apply
ssh.exec_command('pkill -9 -f uvicorn; sleep 2; systemctl start marketview')
time.sleep(5)
i, o, e = ssh.exec_command('systemctl is-active marketview')
print('service:', o.read().decode().strip())
ssh.close()
