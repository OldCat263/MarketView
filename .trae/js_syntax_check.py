"""JS 语法粗验证（括号配对 + 字符串/注释感知）"""
import sys

files = [
    'frontend/js/core.js',
    'frontend/js/kline.js',
    'frontend/js/modules/predict.js',
]

all_ok = True
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        src = fp.read()
    stack = []
    in_str = None
    in_template = False
    in_comment = None
    i = 0
    line = 1
    err = None
    while i < len(src):
        c = src[i]
        if c == '\n':
            line += 1
        if in_comment == 'line':
            if c == '\n':
                in_comment = None
            i += 1
            continue
        if in_comment == 'block':
            if c == '*' and i + 1 < len(src) and src[i + 1] == '/':
                in_comment = None
                i += 2
                continue
            i += 1
            continue
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if in_template:
            if c == '\\':
                i += 2
                continue
            if c == '`':
                in_template = False
            i += 1
            continue
        # 注释起始
        if c == '/' and i + 1 < len(src) and src[i + 1] == '/':
            in_comment = 'line'
            i += 2
            continue
        if c == '/' and i + 1 < len(src) and src[i + 1] == '*':
            in_comment = 'block'
            i += 2
            continue
        # 字符串起始
        if c in ('"', "'"):
            in_str = c
            i += 1
            continue
        if c == '`':
            in_template = True
            i += 1
            continue
        # 括号
        if c in '({[':
            stack.append((c, line))
            i += 1
            continue
        if c in ')}]':
            if not stack:
                err = f'L{line} 多了 {c}'
                break
            op, ol = stack.pop()
            expected = {'(': ')', '{': '}', '[': ']'}[op]
            if expected != c:
                err = f'L{line} {c} 与 L{ol} 的 {op} 不匹配'
                break
            i += 1
            continue
        i += 1
    if err:
        print(f'  X {f}: {err}')
        all_ok = False
    elif stack:
        op, ol = stack[-1]
        print(f'  X {f}: L{ol} 的 {op} 未闭合')
        all_ok = False
    else:
        print(f'  OK {f}: 括号配对 OK')

print('---')
print('ALL OK' if all_ok else 'HAS ERRORS')
sys.exit(0 if all_ok else 1)
