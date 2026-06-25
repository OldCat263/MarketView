"""模块四：港股 — 东财优先，新浪备选"""
import akshare as ak
from .utils import _to_json, _to_records

_source = None

def fetch_shard(shard_idx, total_shards):
    df = ak.stock_hk_spot_em()
    try: recs = _to_records(df)
    except: df = ak.stock_hk_spot(); recs = _to_records(df)
    chunk = max(1, len(recs) // total_shards)
    s = shard_idx * chunk; e = s + chunk if shard_idx < total_shards - 1 else len(recs)
    return recs[s:e]

def get_json():
    global _source
    if _source == 'em':
        try: return _to_json(ak.stock_hk_spot_em())
        except Exception: _source = None
    if _source == 'sina':
        try: return _to_json(ak.stock_hk_spot())
        except Exception: _source = None
    for name, fn in [('em', ak.stock_hk_spot_em), ('sina', ak.stock_hk_spot)]:
        try:
            df = fn(); _source = name
            return _to_json(df)
        except Exception: continue
    return '[]'
