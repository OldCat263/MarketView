# Step 1: write the script with base64
import base64
pw_b64 = base64.b64encode(b'Qwe134679').decode()
script = ''
script += 'import paramiko, time, base64\n'
script += "pw = base64.b64decode(b'%s').decode()\n" % pw_b64
script += 'ssh = paramiko.SSHClient()\n'
script += 'ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())\n'
script += 'ssh.connect("43.156.133.37", username="root", password=*** timeout=10)\n'
script += 'sftp = ssh.open_sftp()\n'
script += "sftp.put(r'D:\\服务器ETF\\backend\\fetcher\\us.py', '/opt/marketview/backend/fetcher/us.py')\n"
script += "sftp.put(r'D:\\服务器ETF\\backend\\main.py', '/opt/marketview/backend/main.py')\n"
script += "sftp.put(r'D:\\服务器ETF\\frontend\\js\\modules\\predict.js', '/opt/marketview/frontend/js/modules/predict.js')\n"
script += "sftp.put(r'D:\\服务器ETF\\frontend\\js\\core.js', '/opt/marketview/frontend/js/core.js')\n"
script += 'sftp.close()\n'
script += "print('pushed 4 files')\n"
script += "ssh.exec_command('find /opt/marketview/backend -name *.pyc -delete')\n"
script += 'ssh.exec_command("pkill -9 -f uvicorn; sleep 2; systemctl start marketview")\n'
script += "print('restarted')\n"
script += 'time.sleep(5)\n'
script += "i, o, e = ssh.exec_command('systemctl is-active marketview')\n"
script += "print('service:', o.read().decode().strip())\n"
script += 'ssh.close()\n'
open(r'D:\服务器ETF\.openclaw\tmp\deploy4.py', 'w', encoding='utf-8').write(script)
print('done')
