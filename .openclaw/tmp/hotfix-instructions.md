## 实施指令：V2.0.1 Hotfix — 7 项代码漏洞修复

### 设计稿
`D:\服务器ETF\docs\V2.0.1-热修复-股票代码前缀.md`

### 改动总览
2 文件 / ~15 行 / 零新依赖

### 分步实施

#### Step 1: `backend/main.py` — `_CODE_PREFIX` 映射函数
在 `from fetcher.utils import _kline_cache, _kline_lock` 后（第 44 行）添加：

```python
# V2.0.1-hotfix: spot 代码转 K线前缀（腾讯 API 需 sh/sz/hk/us）
_CODE_PREFIX = {
    'stock': lambda c: ('sh' if c[0] in ('5','6','9') else 'sz') + c if c.isdigit() and len(c)==6 else c,
    'etf':   lambda c: ('sh' if c[0] in ('5','6','9') else 'sz') + c if c.isdigit() and len(c)==6 else c,
    'hk':    lambda c: 'hk' + c if not c.startswith('hk') else c,
    'us':    lambda c: 'us' + c if not c.startswith('us') else c,
    'index': lambda c: 'sh' + c if c.isdigit() else c,
}
```

#### Step 2: `_precompute_predict()` 修复（~208 行）
原代码：
```python
codes = [r.get('代码', r.get('交易对', '')) for r in spot[:200] if r.get('代码') or r.get('交易对')]
```
改成：
```python
if isinstance(spot, list):
    codes = []
    for r in spot[:200]:
        c = r.get('代码', r.get('交易对', ''))
        if c:
            pf = _CODE_PREFIX.get(m)
            codes.append(pf(c) if pf else c)
else:
    codes = []
```

#### Step 3: `predict_batch()` 修复（~405 行）
原代码：
```python
for r in spot_data[:pool_size]:
    c = r.get('代码', r.get('交易对', ''))
    if c:
        codes.append(c)
```
改成：
```python
if isinstance(spot_data, list):
    for r in spot_data[:pool_size]:
        c = r.get('代码', r.get('交易对', ''))
        if c:
            pf = _CODE_PREFIX.get(module)
            codes.append(pf(c) if pf else c)
```

#### Step 4: `backend/fetcher/scorer.py` — 缓存格式对齐（~23 行）
原代码：
```python
_kline_cache[cache_key] = {'data': {'data': rows}, 'ts': time.time()}
```
改成：
```python
_kline_cache[cache_key] = {'data': rows, 'ts': time.time()}
```
⚠️ 注意：`kline_endpoint` 写缓存时包了完整 `{'data': rows, 'ma': ..., 'boll': ..., 'macd': ...}`，scorer 只存 rows，但读取时 `cached['data']['data']` 这个路径在 kline_endpoint 的缓存上也能工作（因为 kline_endpoint 的 `cached['data']` 本身是完整字典，`['data']` 取 rows）。

#### Step 5: 验证
```bash
# 重启后端
# 等 10s 预热
# BUG1: 批量排行
curl -X POST "http://localhost:8000/api/predict/batch/stock?pool_size=50"
sleep 8
curl -s "http://localhost:8000/api/predict/rank/stock?period=1d&limit=10" | python -m json.tool | head -20

# BUG5: K线缓存有指标
curl -s "http://localhost:8000/api/kline/stock/sh600519?period=1d&count=100" | python -c "import json,sys; d=json.load(sys.stdin); print('ma:', 'ma' in d, 'boll:', 'boll' in d)"

# BUG7: 指数不崩
curl -s "http://localhost:8000/api/predict/rank/index"
```
