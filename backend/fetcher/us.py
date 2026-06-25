"""模块五：美股 — 腾讯 qt.gtimg.cn 优先(线程池并发)，东财/新浪备选"""
import json, time, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

def fetch_shard(shard_idx, total_shards):
    codes = _load_us_codes()
    chunk = max(1, len(codes) // total_shards)
    my = codes[shard_idx*chunk:(shard_idx+1)*chunk] if shard_idx < total_shards-1 else codes[shard_idx*chunk:]
    return _from_tencent_threaded(my, workers=min(3, len(my)//50+1))

_us_codes_cache = None
_us_codes_ts = 0

def _load_us_codes():
    global _us_codes_cache, _us_codes_ts
    now = time.time()
    if _us_codes_cache and now - _us_codes_ts < 86400:
        return _us_codes_cache
    try:
        df = ak.stock_us_spot_em()
        codes = [str(r['代码']) for _, r in df.iterrows()]
    except Exception:
        df = ak.stock_us_spot()
        codes = [str(r.get('symbol','')) for _, r in df.iterrows() if r.get('symbol')]
    _us_codes_cache = codes
    _us_codes_ts = now
    return codes

def _parse_tencent_us(line):
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

def _from_tencent_threaded(codes, workers=11):
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    result = []
    def fetch_batch(batch):
        try:
            url = 'https://qt.gtimg.cn/q=' + ','.join(batch)
            resp = httpx.get(url, timeout=30)
            return [r for r in (_parse_tencent_us(l) for l in resp.text.split('\n')) if r]
        except Exception: return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_batch, b) for b in batches]
        for f in as_completed(futures): result.extend(f.result())
    return result

def get_json():
    try:
        codes = _load_us_codes()
        rows = _from_tencent_threaded(codes)
        if rows: return json.dumps(rows, ensure_ascii=False)
    except Exception as e: print(f'[us] fallback: {e}')
    try: return _to_json(ak.stock_us_spot_em())
    except Exception as e: print(f'[us] fallback: {e}')
    try: return _to_json(ak.stock_us_spot())
    except Exception as e: print(f'[us] fallback: {e}')
    return '[]'
