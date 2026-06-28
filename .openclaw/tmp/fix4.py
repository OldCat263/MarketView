with open(r'D:\服务器ETF\.openclaw\tmp\deploy4.py','rb') as f:
    data = f.read()
data = data.replace(b"sftp.close()", b"sftp.put(r'D:\\服务器ETF\\frontend\\js\\core.js', '/opt/marketview/frontend/js/core.js')\r\nsftp.close()")
data = data.replace(b"print('pushed')", b"print('pushed 4 files')")
with open(r'D:\服务器ETF\.openclaw\tmp\deploy4.py','wb') as f:
    f.write(data)
print('ok')
