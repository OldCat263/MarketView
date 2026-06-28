"""Deploy marketview_mcp.py V2.0.2 to server and run validation."""
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

# Step 0: ensure directory exists
code, out, err = run("mkdir -p /opt/marketview/mcp")
print(f"[OK] mkdir done (exit={code})")

# Step 1: SFTP upload
sftp = client.open_sftp()
sftp.put(r"D:\服务器ETF\mcp\marketview_mcp.py", "/opt/marketview/mcp/marketview_mcp.py")
sftp.close()
print("[OK] SFTP upload done")

# Step 2: Restart
code, out, err = run("systemctl restart marketview")
time.sleep(5)
print(f"[OK] systemctl restart marketview done (exit={code})")

# Step 3: Validation
print("\n--- Version check ---")
code, out, err = run("curl -s http://localhost:8000/api/version")
print(f"  Exit: {code}\n  Out: {out}\n  Err: {err}")

print("\n--- Health check ---")
code, out, err = run("curl -s http://localhost:8000/health")
print(f"  Exit: {code}\n  Out: {out[:500]}")

print("\n--- Import check ---")
code, out, err = run("python3 -c \"import sys; sys.path.insert(0,'/opt/marketview/mcp'); from marketview_mcp import main; print('import OK')\"")
print(f"  Exit: {code}\n  Out: {out}\n  Err: {err}")

print("\n--- Validate script ---")
code, out, err = run("python3 /opt/marketview/mv_validate.py")
print(f"  Exit: {code}")
print(f"  Out:\n{out[:2000]}")
if err:
    print(f"  Err:\n{err[:500]}")

client.close()
print("\n[OK] All checks done")
