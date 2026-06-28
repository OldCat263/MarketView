"""Check server API routes."""
import paramiko

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

# Try different URLs
print("=== Try /api/version ===")
code, out, err = run("curl -sv http://localhost:8000/api/version 2>&1 | head -20")
print(out)

print("\n=== Try /health ===")
code, out, err = run("curl -sv http://localhost:8000/health 2>&1 | head -20")
print(out)

print("\n=== Check backend main.py for endpoints ===")
code, out, err = run("grep -n '@app' /opt/marketview/backend/main.py | head -30")
print(out)

print("\n=== Check if there's a version endpoint ===")
code, out, err = run("grep -n 'version' /opt/marketview/backend/main.py")
print(out)

print("\n=== Try openapi ===")
code, out, err = run("curl -s http://localhost:8000/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(list(d.get('paths',{}).keys())[:20])\"")
print(out)

print("\n=== Backend logs (last 30) ===")
code, out, err = run("journalctl -u marketview --no-pager -n 30")
print(out[:1500])

client.close()
