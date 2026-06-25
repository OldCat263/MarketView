"""模块三：ETF — 东财优先，同花顺备选"""
import akshare as ak
from .utils import _to_json, _to_records

_source = None

def fetch_shard(shard_idx, total_shards):
    """ETF 分片：total_shards=5"""
    df = ak.fund_etf_spot_em()
    recs = _to_records(df)
    chunk = max(1, len(recs) // total_shards)
    start = shard_idx * chunk
    end = start + chunk if shard_idx < total_shards - 1 else len(recs)
    return recs[start:end]

def get_json():
    global _source
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
