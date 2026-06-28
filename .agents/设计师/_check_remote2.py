"""Check server status after deploy."""
import paramiko
import time

host = "43.156.133.37"
port = 22
user = "root"
password = "Qwe134679"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port, user, password)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return exit_status, out, err

print("=== systemctl status ===")
code, out, err = run("systemctl status marketview --no-pager -l")
print(f"exit={code}\nout={out[:800]}\nerr={err[:500]}")

print("\n=== Check port 8000 ===")
code, out, err = run("ss -tlnp | grep 8000")
print(f"out={out}")

print("\n=== Wait 10s then retry ===")
time.sleep(10)
code, out, err = run("curl -s http://localhost:8000/api/version")
print(f"version: {out}")
code, out, err = run("curl -s http://localhost:8000/health | head -c 200")
print(f"health: {out}")

print("\n=== Check for mv_validate.py ===")
code, out, err = run("find /opt/marketview -name 'mv_validate.py' 2>/dev/null")
print(f"find: {out}")

print("\n=== List /opt/marketview/ ===")
code, out, err = run("ls -la /opt/marketview/")
print(f"ls: {out}")

client.close()
