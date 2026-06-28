import re
with open(r'D:\服务器ETF\.openclaw\tmp\push_core.py', 'r', encoding='utf-8') as f:
    txt = f.read()
# Replace 3 sftp.put lines with single core.js put
lines = txt.split('\n')
new_lines = []
for l in lines:
    if 'sftp.put' in l:
        new_lines.append("sftp.put(r'D:\\服务器ETF\\frontend\\js\\core.js', '/opt/marketview/frontend/js/core.js')")
        new_lines.append(l)  # keep one
        continue
    new_lines.append(l)
# Deduplicate: only first sftp.put line
seen = False
final = []
for l in new_lines:
    if 'sftp.put' in l:
        if not seen:
            final.append(l)
            seen = True
        continue
    final.append(l)
txt2 = '\n'.join(final)
txt2 = txt2.replace("print('pushed')", "print('pushed core.js')")
with open(r'D:\服务器ETF\.openclaw\tmp\push_core.py', 'w', encoding='utf-8') as f:
    f.write(txt2)
print('ok')
