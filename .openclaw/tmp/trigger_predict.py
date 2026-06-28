import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password="Qwe134679", timeout=10, allow_agent=False, look_for_keys=False)
stdin, stdout, stderr = c.exec_command("curl -s http://localhost:8000/api/predict/status/stock")
print("STATUS BEFORE:", stdout.read().decode().strip())
# Trigger predict batch
stdin, stdout, stderr = c.exec_command("curl -s -X POST 'http://localhost:8000/api/predict/batch/stock?pool_size=30'")
print("TRIGGER:", stdout.read().decode().strip())
# Wait a bit
import time
time.sleep(3)
# Check status again
stdin, stdout, stderr = c.exec_command("curl -s http://localhost:8000/api/predict/status/stock")
print("STATUS AFTER 3s:", stdout.read().decode().strip())
# Check rank
stdin, stdout, stderr = c.exec_command("curl -s 'http://localhost:8000/api/predict/rank/stock?period=1d&limit=3'")
print("RANK:", stdout.read().decode()[:500])
c.close()
