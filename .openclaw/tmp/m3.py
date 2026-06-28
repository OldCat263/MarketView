with open(r'D:\服务器ETF\.openclaw\tmp\chk8.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("sftp.put(r'D:\\服务器ETF\\backend\\fetcher\\us.py', '/opt/marketview/backend/fetcher/us.py')", "")
c = c.replace("sftp.put(r'D:\\服务器ETF\\backend\\main.py', '/opt/marketview/backend/main.py')", "")
c = c.replace("sftp.put(r'D:\\服务器ETF\\frontend\\js\\modules\\predict.js', '/opt/marketview/frontend/js/modules/predict.js')", "")
c = c.replace("sftp.close()", "")
c = c.replace("print('pushed')", "")
c = c.replace("ssh.exec_command('pkill -9 -f uvicorn; sleep 2; systemctl start marketview')", "")
c = c.replace("print('restarted')", "")
c = c.replace("time.sleep(5)", "")
c = c.replace("print('service:', o.read().decode().strip())", "")
# now just: connect + exec command + close
before = "sftp = ssh.open_sftp()"
after = "i, o, e = ssh.exec_command(" + repr("journalctl -u marketview --no-pager --output=cat -n 15 | grep -E 'predict_daemon|Preload.*done|notified'") + ")\nprint(o.read().decode(errors='replace')[:2000] or 'none')"
c = c.replace(before, after)
with open(r'D:\服务器ETF\.openclaw\tmp\chk8.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('ok')
