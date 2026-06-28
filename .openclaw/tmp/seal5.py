import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password='Qwe134679', timeout=10)

# push MCP
sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\mcp\marketview_mcp.py', '/opt/marketview/mcp/marketview_mcp.py')
sftp.close()
print('[1/4] SFTP OK')

# restart
_, o, _ = ssh.exec_command('systemctl restart marketview')
print('[2/4] restart OK')
time.sleep(10)

# health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('[3/4] health:', o.read().decode(errors='replace')[:200])

# MCP version
_, o, _ = ssh.exec_command('cd /opt/marketview && python3 -c "import sys; sys.path.insert(0,\".\"); from mcp.marketview_mcp import version; print(version())" 2>&1')
print('[4/4] MCP:', o.read().decode(errors='replace')[:200])

ssh.close()
print('done')
