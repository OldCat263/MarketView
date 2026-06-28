import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("43.156.133.37", username="root", password=*** timeout=10, allow_agent=False, look_for_keys=False)
def sh(cmd):
    _, o, _ = c.exec_command(cmd)
    return o.read().decode(errors="replace").strip()
print("STATUS:", sh("curl -s http://localhost:8000/api/predict/status/stock"))
print()
print("RANK:", sh("curl -s " + "'" + "http://localhost:8000/api/predict/rank/stock?period=1d&limit=5" + "'")[:800])
print()
print("HEALTH:", sh("curl -s http://localhost:8000/api/health"))
c.close()