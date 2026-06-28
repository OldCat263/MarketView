import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('43.156.133.37', username='root', password=*** timeout=10)

# 推送 MCP 文件
sftp = ssh.open_sftp()
sftp.put(r'D:\服务器ETF\mcp\marketview_mcp.py', '/opt/marketview/mcp/marketview_mcp.py')
sftp.close()
print('[1/4] MCP 推送 OK')

# 重启
_, o, _ = ssh.exec_command('systemctl restart marketview')
print('[2/4] restart OK')
time.sleep(10)

# 版本
_, o, _ = ssh.exec_command('curl -s http://localhost:8000/api/health 2>&1')
print('[3/4] health:', o.read().decode(errors='replace')[:200])

# MCP import 验证
_, o, _ = ssh.exec_command('cd /opt/marketview && python3 -c "from mcp.marketview_mcp import main; print(main())" 2>&1')
print('[4/4] MCP import:', o.read().decode(errors='replace')[:200])

ssh.close()
print('\n部署完成')
