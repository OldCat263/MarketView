import paramiko
PASS = 'Qwe134679'
host = '43.156.133.37'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=PASS, timeout=10)

_, o, _ = ssh.exec_command("journalctl -u marketview --no-pager -n 100 --output=cat | grep -iE 'predict_daemon|error|traceback|percentile|exception|rank_batch' | tail -30")
print(o.read().decode(errors='replace')[:2000])
ssh.close()
