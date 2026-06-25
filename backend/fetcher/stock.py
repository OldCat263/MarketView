"""模块二：A股 — 腾讯 qt.gtimg.cn 优先，东财/新浪备选"""
import json, httpx, akshare as ak
from .utils import _safe_float, _to_json, _to_records

def _from_tencent():
    codes = [r['代码'] for r in _to_records(ak.stock_zh_a_spot())]
    result = []
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        url = 'https://qt.gtimg.cn/q=' + ','.join(batch)
        resp = httpx.get(url, timeout=30)
        for line in resp.text.split('\n'):
            if '="' not in line: continue
            _, data = line.split('="', 1)
            fields = data.rstrip('";\n').split('~')
            if len(fields) < 45: continue
            result.append({
                '代码': fields[2], '名称': fields[1],
                '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
                '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
                '涨跌额': _safe_float(fields[31]), '涨跌幅': _safe_float(fields[32]),
                '最高': _safe_float(fields[33]), '最低': _safe_float(fields[34]),
                '成交额': _safe_float(fields[37]), '振幅': _safe_float(fields[43]),
                '换手率': _safe_float(fields[38]) if len(fields) > 38 else 0,
                '量比': _safe_float(fields[46]) if len(fields) > 46 else 0,
            })
    return json.dumps(result, ensure_ascii=False)

def get_json():
    for name, fn in [('tx', _from_tencent), ('em', ak.stock_zh_a_spot_em), ('sina', ak.stock_zh_a_spot)]:
        try:
            data = fn()
            return data if isinstance(data, str) else _to_json(data)
        except Exception: continue
    return '[]'
