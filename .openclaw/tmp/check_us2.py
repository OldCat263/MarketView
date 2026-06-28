import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password="Qwe134679", timeout=10)
_, o, _ = c.exec_command("journalctl -u marketview --no-pager -n 1000 --output=cat | grep -E '\\[us\\]' | tail -20")
print(o.read().decode(errors='replace')[:2000])
c.close()
