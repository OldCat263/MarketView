import paramiko
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '43.156.133.37'
USER = 'root'
PASS = 'Qwe134679'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30, banner_timeout=30, auth_timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

# Get verbose output to see blobs decoded
print("=== Verbose journal for predict ===")
log = run("journalctl -u marketview --no-pager --since '15 min ago' -o verbose | grep -A2 'Preload.*predict'")
print(log if log else "(none)", flush=True)

# Also capture ALL output around the precompute startup time
print("\n=== All log around 06:36 (when precompute ran) ===")
log = run("journalctl -u marketview --no-pager --since '2026-06-28 06:36:00' --until '2026-06-28 06:37:00' -o cat")
print(log[:3000] if log else "(empty)", flush=True)

ssh.close()
