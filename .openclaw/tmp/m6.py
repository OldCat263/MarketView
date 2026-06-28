import re
pth = r'D:\服务器ETF\.openclaw\tmp\clean_hk.py'
with open(pth, 'r', encoding='utf-8') as f:
    c = f.read()
# Replace us.py push with hk.py + cache delete
old = "sftp.put(r'D:\\服务器ETF\\backend\\fetcher\\us.py', '/opt/marketview/backend/fetcher/us.py')\n"
new = "sftp.put(r'D:\\服务器ETF\\backend\\fetcher\\hk.py', '/opt/marketview/backend/fetcher/hk.py')\nssh.exec_command('rm -f /opt/marketview/backend/.cache/spot_cache.json /opt/marketview/backend/.cache/kline_cache.json && echo deleted')\n"
c = c.replace(old, new)
with open(pth, 'w', encoding='utf-8') as f:
    f.write(c)
print('ok')
