"""模块三：ETF — 腾讯优先(线程池并发)，东财/同花顺备选"""
import json, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

_source = None

# ETF 代码缓存
_etf_codes_cache = None

def _load_etf_codes():
    global _etf_codes_cache
    if _etf_codes_cache:
        return _etf_codes_cache
    df = ak.fund_etf_spot_em()
    _etf_codes_cache = [str(r['代码']) for _, r in df.iterrows()]
    return _etf_codes_cache

def _parse_tencent_etf(line):
    if '="' not in line: return None
    _, data = line.split('="', 1)
    fields = data.rstrip('";\n').split('~')
    if len(fields) < 35: return None
    return {
        '代码': fields[2], '名称': fields[1],
        '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
        '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
        '涨跌额': _safe_float(fields[31]) if len(fields)>31 else 0,
        '涨跌幅': _safe_float(fields[32]) if len(fields)>32 else 0,
        '最高': _safe_float(fields[33]) if len(fields)>33 else 0,
        '最低': _safe_float(fields[34]) if len(fields)>34 else 0,
        '成交额': _safe_float(fields[37]) if len(fields)>37 else 0,
    }

def _from_tencent_etf(codes, workers=6):
    """腾讯 ETF 批量查询，6 线程并发"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    result = []
    def fetch_batch(batch):
        try:
            url = 'https://qt.gtimg.cn/q=' + ','.join(str(c) for c in batch)
            resp = httpx.get(url, timeout=30)
            return [r for r in (_parse_tencent_etf(l) for l in resp.text.split('\n')) if r]
        except Exception:
            return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_batch, b) for b in batches]
        for f in as_completed(futures): result.extend(f.result())
    return result

def fetch_shard(shard_idx, total_shards):
    """ETF 分片：total_shards=5，优先腾讯并行"""
    codes = _load_etf_codes()
    chunk = max(1, len(codes) // total_shards)
    my = codes[shard_idx*chunk:(shard_idx+1)*chunk] if shard_idx < total_shards-1 else codes[shard_idx*chunk:]
    rows = _from_tencent_etf(my, workers=min(3, len(my)//50+1))
    if rows: return rows
    # 回退 AkShare
    df = ak.fund_etf_spot_em()
    recs = _to_records(df)
    chunk2 = max(1, len(recs) // total_shards)
    start = shard_idx * chunk2
    end = start + chunk2 if shard_idx < total_shards - 1 else len(recs)
    return recs[start:end]

def get_json():
    global _source
    # 优先用腾讯并行
    try:
        codes = _load_etf_codes()
        rows = _from_tencent_etf(codes)
        if rows: return json.dumps(rows, ensure_ascii=False)
    except Exception as e:
        print(f'[etf] tencent err: {e}')
    # 回退 AkShare
    if _source == 'em':
        try: return _to_json(ak.fund_etf_spot_em())
        except Exception as e:
            print(f'[etf] em err: {e}')
            _source = None
    if _source == 'ths':
        try: return _to_json(ak.fund_etf_spot_ths())
        except Exception as e:
            print(f'[etf] ths err: {e}')
            _source = None
    for name, fn in [('em', ak.fund_etf_spot_em), ('ths', ak.fund_etf_spot_ths)]:
        try:
            df = fn(); _source = name
            return _to_json(df)
        except Exception as e:
            print(f'[etf] {name} err: {e}')
            continue
    return '[]'
