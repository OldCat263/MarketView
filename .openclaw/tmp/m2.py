import re
pth = r'D:\服务器ETF\.openclaw\tmp\push5.py'
with open(pth, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace(r'D:\\服务器ETF\\backend\\fetcher\\us.py', r'D:\\服务器ETF\\backend\\main.py')
with open(pth, 'w', encoding='utf-8') as f:
    f.write(c)
print('ok')
