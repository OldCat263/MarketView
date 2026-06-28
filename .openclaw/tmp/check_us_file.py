import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password="Qwe134679", timeout=10)
_, o, _ = c.exec_command("ls -la /opt/marketview/backend/.cache/us_codes.json 2>&1; find /opt/marketview -name 'us_codes.json' 2>/dev/null")
print(o.read().decode(errors='replace')[:500])
c.close()
