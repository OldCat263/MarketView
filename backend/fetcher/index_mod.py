"""模块六：指数 — 东财 push2（国内） + AkShare（全球）分离压力
V2.2.0: 国内指数切东方财富 push2 JSON，全球指数保持 AkShare
"""
import json, httpx, akshare as ak
from .utils import _safe_float, _to_records

_EM_URL = 'https://push2.eastmoney.com/api/qt/clist/get'
_EM_FIELDS = 'f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18,f20'
_EM_FS = 'm:1+s:2,m:0+t:5'

# 白名单：仅核心中国指数
_IDX_CHINA = {'上证指数','深证成指','沪深300','创业板指','科创50','中证500','上证50','深证100'}
_IDX_GLOBAL = {'道琼斯','纳斯达克','标普500','恒生指数','日经225','富时100'}

_IDX_FIELD_MAP = {
    'f2': '最新价', 'f3': '涨跌幅', 'f4': '涨跌额', 'f5': '成交量',
    'f6': '成交额', 'f7': '振幅', 'f12': '代码', 'f14': '名称',
    'f15': '最高', 'f16': '最低', 'f17': '今开', 'f18': '昨收',
    'f20': '总市值',
}


def _from_eastmoney_china():
    """东方财富 push2 国内指数（V2.2.0）"""
    params = {
        'pn': 1, 'pz': 50, 'po': 1, 'np': 1, 'fltt': 2, 'invt': 2,
        'fid': 'f6', 'fs': _EM_FS, 'fields': _EM_FIELDS,
    }
    resp = httpx.get(_EM_URL, params=params, timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                              'Referer': 'https://www.eastmoney.com'},
                     follow_redirects=True)
    data = resp.json()
    diffs = data.get('data', {}).get('diff', []) or []
    rows = []
    for d in diffs:
        name = d.get('f14', '')
        if name not in _IDX_CHINA:
            continue
        row = {}
        for fk, col_name in _IDX_FIELD_MAP.items():
            val = d.get(fk)
            if val == '-' or val is None:
                val = 0
            row[col_name] = _safe_float(val) if col_name not in ('代码', '名称') else val
        rows.append(row)
    return rows


def fetch_shard(shard_idx, total_shards):
    result = get_json()
    data = json.loads(result)
    if total_shards <= 1:
        return data
    all_rows = data.get('china', []) + data.get('global', [])
    chunk = max(1, len(all_rows) // total_shards)
    s = shard_idx * chunk; e = s + chunk if shard_idx < total_shards - 1 else len(all_rows)
    return all_rows[s:e]


def get_json():
    """指数实时行情 — 国内：东财 push2（V2.2.0），全球：AkShare"""
    try:
        china = _from_eastmoney_china()
    except Exception as e:
        print(f'[index] eastmoney err: {e}', flush=True)
        china = []
    try:
        g = ak.index_global_spot_em()
        global_list = [r for r in _to_records(g) if r.get('名称','') in _IDX_GLOBAL]
    except Exception as e:
        print(f'[index] global em err: {e}', flush=True)
        global_list = []
    return json.dumps({'global': global_list, 'china': china}, ensure_ascii=False)
