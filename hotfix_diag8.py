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

# Show all logs since the last restart
print("=== All logs since restart ===")
log = run("journalctl -u marketview --no-pager --since '15 min ago' | grep -v 'SettingWithCopyWarning\|pd.to_numeric\|temp_df\|See the caveats\|Try using\|A value is trying\|df\\[col\\]' | tail -40")
print(log, flush=True)

# Specifically look for predict precompute
print("\n=== Predict precompute logs ===")
log = run("journalctl -u marketview --no-pager --since '15 min ago' | grep -E 'Preload.*predict|predict.*ranked|predict.*err'")
print(log if log else "(none)", flush=True)

ssh.close()
