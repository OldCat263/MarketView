"""模块四：港股 — 腾讯优先(线程池并发)，东财/新浪备选"""
import json, time, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

_source = None

# 港股代码缓存
_hk_codes_cache = None
_hk_codes_ts = 0

def _load_hk_codes():
    global _hk_codes_cache, _hk_codes_ts
    now = time.time()
    if _hk_codes_cache and now - _hk_codes_ts < 86400:
        return _hk_codes_cache
    try:
        df = ak.stock_hk_spot_em()
        codes = [str(r['代码']) for _, r in df.iterrows()]
    except Exception:
        df = ak.stock_hk_spot()
        codes = [str(r.get('代码','')) for _, r in df.iterrows() if r.get('代码')]
    _hk_codes_cache = codes
    _hk_codes_ts = now
    return codes

def _from_tencent_hk(codes, workers=6):
    """腾讯港股并行获取 — 50只/请求, hk前缀"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    result = []
    def fetch_batch(batch):
        try:
            codes_clean = [str(c) for c in batch]
            url = 'https://qt.gtimg.cn/q=' + ','.join('hk' + c for c in codes_clean)
            resp = httpx.get(url, timeout=30)
            rows = []
            for line in resp.text.split('\n'):
                if '="' not in line: continue
                _, data = line.split('="', 1)
                fields = data.rstrip('";\n').split('~')
                if len(fields) < 35: continue
                rows.append({
                    '代码': fields[2], '名称': fields[1],
                    '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
                    '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
                    '涨跌额': _safe_float(fields[31]) if len(fields)>31 else 0,
                    '涨跌幅': _safe_float(fields[32]) if len(fields)>32 else 0,
                    '最高': _safe_float(fields[33]) if len(fields)>33 else 0,
                    '最低': _safe_float(fields[34]) if len(fields)>34 else 0,
                    '成交额': _safe_float(fields[37]) if len(fields)>37 else 0,
                })
            return rows
        except Exception:
            return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_batch, b) for b in batches]
        for f in as_completed(futures): result.extend(f.result())
    return result

def fetch_shard(shard_idx, total_shards):
    # 优先用腾讯并行
    codes = _load_hk_codes()
    chunk = max(1, len(codes) // total_shards)
    my = codes[shard_idx*chunk:(shard_idx+1)*chunk] if shard_idx < total_shards-1 else codes[shard_idx*chunk:]
    rows = _from_tencent_hk(my)
    if rows: return rows
    # 回退 AkShare
    recs = None
    for fn in [ak.stock_hk_spot_em, ak.stock_hk_spot]:
        try:
            recs = _to_records(fn())
            if recs: break
        except Exception as e:
            print(f'[hk] fetch_shard source err: {e}')
    if not recs: return []
    chunk2 = max(1, len(recs) // total_shards)
    s = shard_idx * chunk2; e = s + chunk2 if shard_idx < total_shards - 1 else len(recs)
    return recs[s:e]

def get_json():
    global _source
    # 优先用腾讯并行
    try:
        codes = _load_hk_codes()
        rows = _from_tencent_hk(codes)
        if rows: return json.dumps(rows, ensure_ascii=False)
    except Exception as e:
        print(f'[hk] tencent err: {e}')
    # 回退 AkShare
    if _source == 'em':
        try: return _to_json(ak.stock_hk_spot_em())
        except Exception as e:
            print(f'[hk] em err: {e}')
            _source = None
    if _source == 'sina':
        try: return _to_json(ak.stock_hk_spot())
        except Exception as e:
            print(f'[hk] sina err: {e}')
            _source = None
    for name, fn in [('em', ak.stock_hk_spot_em), ('sina', ak.stock_hk_spot)]:
        try:
            df = fn(); _source = name
            return _to_json(df)
        except Exception as e:
            print(f'[hk] {name} err: {e}')
            continue
    return '[]'
