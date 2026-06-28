import paramiko, subprocess, sys
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password="Qwe134679", timeout=10, allow_agent=False, look_for_keys=False)
stdin, stdout, stderr = c.exec_command("grep -n -E '_stock_prefix|_CODE_PREFIX' /opt/marketview/backend/main.py")
print(stdout.read().decode()[:500])
c.close()