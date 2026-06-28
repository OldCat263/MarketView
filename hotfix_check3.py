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

# Show full _do_batch
print("=== Full _do_batch ===")
code = run("sed -n '428,470p' /opt/marketview/backend/main.py")
print(code, flush=True)

# Show _precompute_predict  
print("\n=== Full _precompute_predict ===")
code = run("sed -n '216,260p' /opt/marketview/backend/main.py")
print(code, flush=True)

ssh.close()
