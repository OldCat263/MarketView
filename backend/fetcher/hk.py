"""模块四：港股 — 腾讯优先(线程池并发)，东财/新浪备选
V2.0.3: 白名单过滤 ~200 只（A+H两地上市 + 恒生科技 + 蓝筹 + ETF）
"""
import json, time, httpx, akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import _safe_float, _to_json, _to_records

# V2.0.3: 港股白名单 ~200 只（A+H两地上市+恒生科技+蓝筹+ETF），过滤港股几千只仙股
_HK_WHITELIST = {
    # A+H 两地上市
    '00386','00857','00939','00941','01088','01171','01186','01211','01336','01339','01398',
    '01618','01766','01776','01812','01898','01919','01958','01988','02009','02016','02018',
    '02068','02196','02202','02238','02318','02333','02338','02380','02600','02601','02607',
    '02611','02628','02696','02727','02866','02883','03328','03333','03369','03380','03606',
    '03618','03866','03898','03968','03988','00358','00525','00564','00588','00670','00902',
    '01033','01053','01055','01071','01108','01133','01138','01288','01317','01330','01375',
    '01456','01513','01635','01763','01787','01799','01800','01816','01839','01963','02039',
    '02128','02208','02218','02496','02518','02617','02799','02880','03369','03389','03477',
    '00656','00699','02382','09988','09618','09888','09999','09626','09899','09660',
    # 恒生科技龙头
    '00700','03690','01024','09992','01810','02015','09618','09626','01020','06618',
    '01050','09988','09961','09878','02562',
    # 港股特色蓝筹
    '00001','00002','00003','00005','00006','00011','00012','00016','00017','00019',
    '00027','00066','00083','00101','00175','00267','00268','00288','00291','00316',
    '00322','00388','00669','00762','00823','00883','00941','01044','01109','01113',
    '01299','01928','01929','02269','02313','02319','02331','02899','06862','09633',
    # 知名 ETF
    '02800','02828','02823','03188','03033','03067','02822','03110',
}

def _filter_hk(rows):
    """白名单过滤港股"""
    return [r for r in rows if str(r.get('代码','') or r.get('code','')) in _HK_WHITELIST]

_source = None

# 港股代码缓存
_hk_codes_cache = None
_hk_codes_ts = 0

def _load_hk_codes():
    global _hk_codes_cache, _hk_codes_ts
    now = time.time()
    if _hk_codes_cache and now - _hk_codes_ts < 86400:
        return _hk_codes_cache
    try:
        df = ak.stock_hk_spot_em()
        codes = [str(r['代码']) for _, r in df.iterrows() if str(r['代码']) in _HK_WHITELIST]
    except Exception:
        df = ak.stock_hk_spot()
        codes = [str(r.get('代码','')) for _, r in df.iterrows() if r.get('代码') and str(r.get('代码','')) in _HK_WHITELIST]
    _hk_codes_cache = codes
    _hk_codes_ts = now
    return codes

def _from_tencent_hk(codes, workers=6):
    """腾讯港股并行获取 — 50只/请求, hk前缀"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    result = []
    def fetch_batch(batch):
        try:
            codes_clean = [str(c) for c in batch]
            url = 'https://qt.gtimg.cn/q=' + ','.join('hk' + c for c in codes_clean)
            resp = httpx.get(url, timeout=30)
            rows = []
            for line in resp.text.split('\n'):
                if '="' not in line: continue
                _, data = line.split('="', 1)
                fields = data.rstrip('";\n').split('~')
                if len(fields) < 35: continue
                rows.append({
                    '代码': fields[2], '名称': fields[1],
                    '最新价': _safe_float(fields[3]), '昨收': _safe_float(fields[4]),
                    '今开': _safe_float(fields[5]), '成交量': _safe_float(fields[6]),
                    '涨跌额': _safe_float(fields[31]) if len(fields)>31 else 0,
                    '涨跌幅': _safe_float(fields[32]) if len(fields)>32 else 0,
                    '最高': _safe_float(fields[33]) if len(fields)>33 else 0,
                    '最低': _safe_float(fields[34]) if len(fields)>34 else 0,
                    '成交额': _safe_float(fields[37]) if len(fields)>37 else 0,
                })
            return rows
        except Exception:
            return []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fetch_batch, b) for b in batches]
        for f in as_completed(futures): result.extend(f.result())
    return result

def fetch_shard(shard_idx, total_shards):
    # 优先用腾讯并行
    codes = _load_hk_codes()
    chunk = max(1, len(codes) // total_shards)
    my = codes[shard_idx*chunk:(shard_idx+1)*chunk] if shard_idx < total_shards-1 else codes[shard_idx*chunk:]
    rows = _from_tencent_hk(my)
    rows = _filter_hk(rows)
    if rows: return rows
    # 回退 AkShare
    recs = None
    for fn in [ak.stock_hk_spot_em, ak.stock_hk_spot]:
        try:
            recs = _to_records(fn())
            if recs: break
        except Exception as e:
            print(f'[hk] fetch_shard source err: {e}')
    if not recs: return []
    recs = _filter_hk(recs)
    chunk2 = max(1, len(recs) // total_shards)
    s = shard_idx * chunk2; e = s + chunk2 if shard_idx < total_shards - 1 else len(recs)
    return recs[s:e]

def get_json():
    global _source
    # 优先用腾讯并行
    try:
        codes = _load_hk_codes()
        rows = _from_tencent_hk(codes)
        rows = _filter_hk(rows)
        if rows: return json.dumps(rows, ensure_ascii=False)
    except Exception as e:
        print(f'[hk] tencent err: {e}')
    # 回退 AkShare
    if _source == 'em':
        try: return _to_json(_filter_hk(_to_records(ak.stock_hk_spot_em())))
        except Exception as e:
            print(f'[hk] em err: {e}')
            _source = None
    if _source == 'sina':
        try: return _to_json(_filter_hk(_to_records(ak.stock_hk_spot())))
        except Exception as e:
            print(f'[hk] sina err: {e}')
            _source = None
    for name, fn in [('em', ak.stock_hk_spot_em), ('sina', ak.stock_hk_spot)]:
        try:
            df = fn(); _source = name
            return _to_json(_filter_hk(_to_records(df)))
        except Exception as e:
            print(f'[hk] {name} err: {e}')
            continue
    return '[]'
