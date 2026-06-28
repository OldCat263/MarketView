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

# The blobs are important - they contain error messages. Let's decode them.
print("=== Raw journal output with catalog ===")
log = run("journalctl -u marketview --no-pager --since '15 min ago' --output=cat | grep -i 'predict\|error\|exception\|traceback' | tail -20")
print(log if log else "(none)", flush=True)

# Check the lifepsan function for the precompute startup
print("\n=== Lifespan function ===")
code = run("sed -n '180,250p' /opt/marketview/backend/main.py")
print(code, flush=True)

ssh.close()
