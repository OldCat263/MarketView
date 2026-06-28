import paramiko, time
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password="Qwe134679", timeout=10)
_, o, _ = c.exec_command("journalctl -u marketview --no-pager -n 200 --output=cat | tail -50")
print(o.read().decode(errors='replace'))
c.close()
