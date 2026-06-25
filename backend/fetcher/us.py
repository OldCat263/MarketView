"""模块五：美股 — 东财优先，新浪备选"""
import akshare as ak
from .utils import _to_json

_source = None

def get_json():
    global _source
    if _source == 'em':
        try: return _to_json(ak.stock_us_spot_em())
        except Exception: _source = None
    if _source == 'sina':
        try: return _to_json(ak.stock_us_spot())
        except Exception: _source = None
    for name, fn in [('em', ak.stock_us_spot_em), ('sina', ak.stock_us_spot)]:
        try:
            df = fn(); _source = name
            return _to_json(df)
        except Exception: continue
    return '[]'
