"""Final validation checks for V2.0.2."""
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

print("=== 1. Version check (openapi) ===")
code, out, err = run("curl -s http://localhost:8000/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print('title:', d.get('info',{}).get('title'), '| version:', d.get('info',{}).get('version'))\"")
print(f"  {out}")

print("\n=== 2. Health check ===")
code, out, err = run("curl -s http://localhost:8000/api/health")
print(f"  {out[:300]}")

print("\n=== 3. MCP version check (from deployed file) ===")
code, out, err = run("grep 'mcp_version' /opt/marketview/mcp/marketview_mcp.py")
print(f"  {out}")

print("\n=== 4. Verify asyncio import in deployed MCP ===")
code, out, err = run("grep 'import asyncio' /opt/marketview/mcp/marketview_mcp.py")
print(f"  {out}")

print("\n=== 5. Verify all V2.0.2 in deployed MCP ===")
code, out, err = run("grep 'V2.0.2' /opt/marketview/mcp/marketview_mcp.py")
print(f"  {out}")

print("\n=== 6. MCP import check ===")
code, out, err = run("python3 -c \"import sys; sys.path.insert(0,'/opt/marketview/mcp'); import py_compile; py_compile.compile('/opt/marketview/mcp/marketview_mcp.py', doraise=True); print('Syntax OK')\"")
print(f"  exit={code} out={out} err={err}")

print("\n=== 7. Validate script ===")
code, out, err = run("python3 /opt/marketview/.trae/skills/mv-validator/scripts/mv_validate.py")
print(f"  exit={code}")
print(f"  out:\n{out[:2000]}")
if err:
    print(f"  err:\n{err[:500]}")

print("\n=== 8. Check no V2.0.1 left ===")
code, out, err = run("grep 'V2.0.1' /opt/marketview/mcp/marketview_mcp.py; echo \"exit=$?\"")
print(f"  {out}")

client.close()
