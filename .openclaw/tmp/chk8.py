import paramiko, time, base64
pw = base64.b64decode(b'UXdlMTM0Njc5').decode()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=pw, timeout=10)
i, o, e = ssh.exec_command("journalctl -u marketview --no-pager --output=cat -n 15 | grep -E 'predict_daemon|Preload.*done|notified'")
print(o.read().decode(errors='replace')[:2000] or 'none')








i, o, e = ssh.exec_command('systemctl is-active marketview')

ssh.close()
