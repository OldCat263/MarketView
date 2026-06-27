"""模块五：美股 — 腾讯 qt.gtimg.cn 优先(线程池并发)，东财/新浪备选"""
import json, time, os, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

_US_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.cache', 'us_codes.json')

def fetch_shard(shard_idx, total_shards):
    codes = _load_us_codes()
    # V1.8.6: 分片 0 先拉热门股（前 100 只）
    if shard_idx == 0:
        return _from_tencent_threaded(codes[:100], workers=3)
    # 其余分片覆盖 codes[100:] 全量，无缺口
    rest = codes[100:]
    n_rest = total_shards - 1
    chunk = max(1, len(rest) // n_rest)
    my_idx = shard_idx - 1
    my = rest[my_idx*chunk:(my_idx+1)*chunk] if my_idx < n_rest-1 else rest[my_idx*chunk:]
    return _from_tencent_threaded(my, workers=min(3, len(my)//50+1))

_us_codes_cache = None
_us_codes_ts = 0

def _load_us_codes():
    global _us_codes_cache, _us_codes_ts
    now = time.time()
    if _us_codes_cache and now - _us_codes_ts < 86400:
        return _us_codes_cache
    # 尝试磁盘缓存
    if _us_codes_cache is None and os.path.exists(_US_CODES_FILE):
        try:
            with open(_US_CODES_FILE, 'r', encoding='utf-8') as f:
                _us_codes_cache = json.load(f)
            _us_codes_ts = now
            return _us_codes_cache
        except Exception:
            pass
    # 回退到 AkShare
    try:
        df = ak.stock_us_spot_em()
        codes_with_vol = [(str(r['代码']), float(r.get('成交量', 0) or 0)) for _, r in df.iterrows()]
        codes_with_vol.sort(key=lambda x: x[1], reverse=True)  # 成交量降序，热门在前
        codes = [c for c, _ in codes_with_vol]
    except Exception:
        df = ak.stock_us_spot()
        codes = [str(r.get('symbol','')) for _, r in df.iterrows() if r.get('symbol')]
    _us_codes_cache = codes
    _us_codes_ts = now
    # 持久化
    try:
        os.makedirs(os.path.dirname(_US_CODES_FILE), exist_ok=True)
        with open(_US_CODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(codes, f)
    except Exception:
        pass
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
            # 腾讯需要 us 前缀 + 去后缀（AAPL.OQ → usAAPL）
            codes_clean = [str(c).replace('.OQ','').replace('.N','').replace('.AM','') for c in batch]
            url = 'https://qt.gtimg.cn/q=' + ','.join('us' + c for c in codes_clean)
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
