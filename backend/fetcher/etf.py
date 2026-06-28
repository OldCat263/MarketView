"""模块三：ETF — 东方财富 push2 JSON API（V2.2.0 不再共用腾讯，独立压力）
V2.2.0: 切东方财富 push2 JSON（4线程并发），脱离腾讯（留给 hk/us）
"""
import json, httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float

_EM_URL = 'https://push2.eastmoney.com/api/qt/clist/get'
_EM_FS = 'b:MK0021,b:MK0022,b:MK0023,b:MK0024,b:MK0025,b:MK0026,b:MK0027,b:MK0028,b:MK0029,b:MK0030,b:MK0031,b:MK0032,b:MK0033,b:MK0034,b:MK0035,b:MK0036,b:MK0037,b:MK0038,b:MK0039,b:MK0040,b:MK0041,b:MK0042,b:MK0043,b:MK0044,b:MK0045,b:MK0046,b:MK0047,b:MK0048,b:MK0049,b:MK0050'
_EM_FIELDS = 'f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18'
_PZ = 100

_ETF_FIELD_MAP = {
    'f2': '最新价', 'f3': '涨跌幅', 'f4': '涨跌额', 'f5': '成交量',
    'f6': '成交额', 'f7': '振幅', 'f12': '代码', 'f14': '名称',
    'f15': '最高价', 'f16': '最低价', 'f17': '今开', 'f18': '昨收',
}


def _eastmoney_page(pn, pz=_PZ):
    params = {
        'pn': pn, 'pz': pz, 'po': 1, 'np': 1, 'fltt': 2, 'invt': 2,
        'fid': 'f3', 'fs': _EM_FS, 'fields': _EM_FIELDS,
    }
    resp = httpx.get(_EM_URL, params=params, timeout=15)
    data = resp.json()
    total = data.get('data', {}).get('total', 1626)
    diffs = data.get('data', {}).get('diff', []) or []
    rows = []
    for d in diffs:
        row = {}
        for fk, name in _ETF_FIELD_MAP.items():
            val = d.get(fk)
            if val == '-' or val is None:
                val = 0
            row[name] = _safe_float(val) if name not in ('代码', '名称') else val
        rows.append(row)
    return rows, total


def _from_eastmoney_full():
    """全量拉取（~17 页 pz=100，4 线程并发 ~2s）"""
    _, total = _eastmoney_page(1, 1)
    total_pages = (total + _PZ - 1) // _PZ

    def _fetch_page(pn):
        return _eastmoney_page(pn)[0]

    all_rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_fetch_page, pn): pn for pn in range(1, total_pages + 1)}
        for f in as_completed(futures):
            all_rows.extend(f.result())
    return all_rows


def fetch_shard(shard_idx, total_shards):
    _, total = _eastmoney_page(1, 1)
    pp_shard = max(1, (total // total_shards + 1) // _PZ + 1)
    rows = []
    for i in range(pp_shard):
        pn = shard_idx * pp_shard + i + 1
        page_rows, _ = _eastmoney_page(pn)
        rows.extend(page_rows)
    return rows


def get_json():
    """ETF实时行情 — 东方财富 push2 JSON（V2.2.0）"""
    try:
        rows = _from_eastmoney_full()
        return json.dumps(rows, ensure_ascii=False) if rows else '[]'
    except Exception as e:
        print(f'[etf] eastmoney err: {e}', flush=True)
        return '[]'
