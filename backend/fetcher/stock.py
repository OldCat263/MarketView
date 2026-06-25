"""模块二：A股 — 腾讯 qt.gtimg.cn 优先，东财/新浪备选"""
import json, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

def _parse_tencent_line(line):
    if '="' not in line: return None
    _, data = line.split('="', 1)
    fields = data.rstrip('";\n').split('~')
    if len(fields) < 45: return None
    return {
        '代码': fields[2], '名称': fields[1],
        '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
        '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
        '涨跌额': _safe_float(fields[31]), '涨跌幅': _safe_float(fields[32]),
        '最高': _safe_float(fields[33]), '最低': _safe_float(fields[34]),
        '成交额': _safe_float(fields[37]), '振幅': _safe_float(fields[43]),
        '换手率': _safe_float(fields[38]) if len(fields) > 38 else 0,
        '量比': _safe_float(fields[46]) if len(fields) > 46 else 0,
    }

def _from_tencent_threaded(codes, workers=11):
    """腾讯批量查询，11线程并发"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    result = []
    def fetch_batch(batch):
        try:
            url = 'https://qt.gtimg.cn/q=' + ','.join(batch)
            resp = httpx.get(url, timeout=30)
            return [r for r in (_parse_tencent_line(l) for l in resp.text.split('\n')) if r]
        except Exception:
            return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_batch, b) for b in batches]
        for f in as_completed(futures):
            result.extend(f.result())
    return result

def get_json():
    """A 股实时行情 — 腾讯线程池并发优先"""
    try:
        codes = [r['代码'] for r in _to_records(ak.stock_zh_a_spot())]
        rows = _from_tencent_threaded(codes)
        return json.dumps(rows, ensure_ascii=False)
    except Exception: pass
    try: return _to_json(ak.stock_zh_a_spot_em())
    except Exception: pass
    try: return _to_json(ak.stock_zh_a_spot())
    except Exception: pass
    return '[]'
