"""Check remote structure then upload."""
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

# Check what exists
for d in ["/opt/marketview", "/opt/marketview/mcp"]:
    code, out, err = run(f"ls -la {d}")
    print(f"\n{d}: exit={code}, out={out[:300]}, err={err[:300]}")

client.close()
