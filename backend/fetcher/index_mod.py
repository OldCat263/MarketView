"""模块六：指数 — 东财优先，新浪备选"""
import json, akshare as ak
from .utils import _to_records

_source = None

def fetch_shard(shard_idx, total_shards):
    result = get_json()
    data = json.loads(result)
    all_rows = data.get('china', []) + data.get('global', [])
    if total_shards <= 1: return all_rows
    chunk = max(1, len(all_rows) // total_shards)
    s = shard_idx * chunk; e = s + chunk if shard_idx < total_shards - 1 else len(all_rows)
    return all_rows[s:e]

def get_json():
    global _source
    if _source == 'em':
        try: return _from_em()
        except Exception: _source = None
    if _source == 'sina':
        try: return _from_sina()
        except Exception: _source = None
    for name, fn in [('em', _from_em), ('sina', _from_sina)]:
        try:
            result = fn(); _source = name
            return result
        except Exception: continue
    return '{}'

def _from_em():
    g = ak.index_global_spot_em()
    c = ak.stock_zh_index_spot_em()
    return json.dumps({'global': _to_records(g), 'china': _to_records(c)}, ensure_ascii=False)

def _from_sina():
    c = ak.stock_zh_index_spot_sina()
    try: g = ak.index_global_spot_em()
    except Exception: g = None
    return json.dumps({'global': _to_records(g), 'china': _to_records(c)}, ensure_ascii=False)
