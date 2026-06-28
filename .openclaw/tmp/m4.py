pth = r'D:\服务器ETF\.openclaw\tmp\push_idx.py'
with open(pth, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace(r'D:\\服务器ETF\\backend\\fetcher\\us.py', r'D:\\服务器ETF\\backend\\fetcher\\index_mod.py')
with open(pth, 'w', encoding='utf-8') as f:
    f.write(c)
print('ok')
