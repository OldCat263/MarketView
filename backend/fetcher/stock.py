"""模块二：A股 — 东方财富 push2 JSON API（V2.2.0 不再共用腾讯，独立压力）
V2.2.0: 切东方财富 push2 JSON（~5534只/56页 pz=100，4线程并发 ~5s），脱离腾讯（留给 hk/us）
"""
import json, httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float

_EM_URL = 'https://push2.eastmoney.com/api/qt/clist/get'
_EM_FS = 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23'
_EM_FIELDS = 'f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23'
_PZ = 100  # push2 每页最大 100 只

# 字段映射
_STOCK_FIELD_MAP = {
    'f2': '最新价', 'f3': '涨跌幅', 'f4': '涨跌额', 'f5': '成交量',
    'f6': '成交额', 'f7': '振幅', 'f8': '换手率', 'f9': '市盈率',
    'f10': '量比', 'f12': '代码', 'f14': '名称',
    'f15': '最高', 'f16': '最低', 'f17': '今开', 'f18': '昨收',
    'f20': '总市值', 'f21': '流通市值', 'f23': '市净率',
}


def _eastmoney_page(pn, pz=_PZ):
    """单页查询"""
    params = {
        'pn': pn, 'pz': pz, 'po': 1, 'np': 1, 'fltt': 2, 'invt': 2,
        'fid': 'f3', 'fs': _EM_FS, 'fields': _EM_FIELDS,
    }
    resp = httpx.get(_EM_URL, params=params, timeout=15)
    data = resp.json()
    total = data.get('data', {}).get('total', 5534)
    diffs = data.get('data', {}).get('diff', []) or []
    rows = []
    for d in diffs:
        row = {}
        for fk, name in _STOCK_FIELD_MAP.items():
            val = d.get(fk)
            if val == '-' or val is None:
                val = 0
            row[name] = _safe_float(val) if name not in ('代码', '名称') else val
        rows.append(row)
    return rows, total


def _from_eastmoney_full():
    """全量拉取（~56 页 pz=100，4 线程并发 ~5s）"""
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


def _pages_per_shard(total, shards):
    """计算每分片负责的页数"""
    rows_per_shard = total // shards + 1
    pages = rows_per_shard // _PZ + (1 if rows_per_shard % _PZ else 0)
    return max(1, pages)


def fetch_shard(shard_idx, total_shards):
    """分片获取：每个 shard 负责若干连续页（并行滚动，互不重叠）"""
    # 首批：探测总数
    _, total = _eastmoney_page(1, 1)
    pp_shard = _pages_per_shard(total, total_shards)
    rows = []
    for i in range(pp_shard):
        pn = shard_idx * pp_shard + i + 1
        page_rows, _ = _eastmoney_page(pn)
        rows.extend(page_rows)
    return rows


def get_json():
    """A股实时行情 — 东方财富 push2 JSON（V2.2.0）"""
    try:
        rows = _from_eastmoney_full()
        return json.dumps(rows, ensure_ascii=False) if rows else '[]'
    except Exception as e:
        print(f'[stock] eastmoney err: {e}', flush=True)
        return '[]'
