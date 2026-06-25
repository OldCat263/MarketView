"""模块三：ETF — 东财优先，同花顺备选"""
import akshare as ak
from .utils import _to_json

_source = None

def get_json():
    global _source
    if _source == 'em':
        try: return _to_json(ak.fund_etf_spot_em())
        except Exception: _source = None
    if _source == 'ths':
        try: return _to_json(ak.fund_etf_spot_ths())
        except Exception: _source = None
    for name, fn in [('em', ak.fund_etf_spot_em), ('ths', ak.fund_etf_spot_ths)]:
        try:
            df = fn(); _source = name
            return _to_json(df)
        except Exception: continue
    return '[]'
