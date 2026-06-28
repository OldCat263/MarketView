import paramiko, time, base64
pw = base64.b64decode(b'UXdlMTM0Njc5').decode()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)






i, o, e = ssh.exec_command('systemctl is-active marketview')

ssh.close()

i, o, e = ssh.exec_command('head -5 /opt/marketview/backend/fetcher/hk.py; grep -c _HK_WHITELIST /opt/marketview/backend/fetcher/hk.py')
print(o.read().decode().strip())
