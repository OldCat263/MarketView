import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)

sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\mcp\marketview_mcp.py', '/opt/marketview/mcp/marketview_mcp.py')
sftp.close()
print('SFTP OK')

_, o, _ = ssh.exec_command('systemctl restart marketview')
print('restart OK')

import time
time.sleep(8)

# 验收 1: 版本
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/version')
print('version:', o.read().decode(errors='replace')[:200])

# 验收 2: health
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health')
print('health:', o.read().decode(errors='replace')[:200])

# 验收 3: MCP import
_, o, _ = ssh.exec_command('python3 -c "import sys; sys.path.insert(0,\"/opt/marketview/mcp\"); from marketview_mcp import main; print(\"import OK\")"')
print('MCP import:', o.read().decode(errors='replace')[:100])

# 验收 4: mv_validate
_, o, _ = ssh.exec_command('python3 /opt/marketview/mv_validate.py 2>&1 | head -30')
out = o.read().decode(errors='replace')
print('validate:', out[:500])

ssh.close()
