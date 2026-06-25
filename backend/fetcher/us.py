"""模块五：美股 — 腾讯 qt.gtimg.cn 优先(并发)，东财/新浪备选"""
import json, time, asyncio, httpx, akshare as ak
from .utils import _safe_float, _to_json, _to_records

# 美股代码列表缓存（1天TTL，内存变量）
_us_codes_cache = None
_us_codes_ts = 0

def _load_us_codes():
    """加载美股代码列表，缓存1天"""
    global _us_codes_cache, _us_codes_ts
    now = time.time()
    if _us_codes_cache and now - _us_codes_ts < 86400:
        return _us_codes_cache
    try:
        df = ak.stock_us_spot_em()
        codes = [str(r['代码']) for _, r in df.iterrows()]
        _us_codes_cache = codes
        _us_codes_ts = now
        return codes
    except Exception:
        # Fallback to Sina
        df = ak.stock_us_spot()
        codes = [str(r.get('symbol','')) for _, r in df.iterrows() if r.get('symbol')]
        _us_codes_cache = codes
        _us_codes_ts = now
        return codes

def _parse_tencent_us(line):
    """解析腾讯美股行 → dict"""
    if '="' not in line: return None
    _, data = line.split('="', 1)
    fields = data.rstrip('";\n').split('~')
    if len(fields) < 35: return None
    return {
        '代码': fields[2], '名称': fields[1],
        '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
        '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
        '涨跌额': _safe_float(fields[31]) if len(fields) > 31 else 0,
        '涨跌幅': _safe_float(fields[32]) if len(fields) > 32 else 0,
        '最高': _safe_float(fields[33]) if len(fields) > 33 else 0,
        '最低': _safe_float(fields[34]) if len(fields) > 34 else 0,
        '成交额': _safe_float(fields[37]) if len(fields) > 37 else 0,
    }

async def _from_tencent_concurrent(codes, concurrency=11):
    """腾讯美股批量查询，并发"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    sem = asyncio.Semaphore(concurrency)
    result = []
    async def fetch_one(batch):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                    url = 'https://qt.gtimg.cn/q=' + ','.join(batch)
                    resp = await client.get(url)
                    return [r for r in (_parse_tencent_us(l) for l in resp.text.split('\n')) if r]
            except Exception: return []
    tasks = [fetch_one(b) for b in batches]
    batch_results = await asyncio.gather(*tasks)
    for br in batch_results: result.extend(br)
    return result

async def get_json():
    """美股实时行情 — 腾讯并发优先"""
    try:
        codes = _load_us_codes()
        rows = await _from_tencent_concurrent(codes)
        if rows: return json.dumps(rows, ensure_ascii=False)
    except Exception: pass
    try: return _to_json(ak.stock_us_spot_em())
    except Exception: pass
    try: return _to_json(ak.stock_us_spot())
    except Exception: pass
    return '[]'
