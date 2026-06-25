"""模块二：A股 — 腾讯 qt.gtimg.cn 优先(并发11路)，东财/新浪备选"""
import json, asyncio, httpx, akshare as ak
from .utils import _safe_float, _to_json, _to_records

def _parse_tencent_line(line):
    """解析腾讯单行 → dict"""
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

async def _from_tencent_concurrent(codes: list, concurrency: int = 11):
    """腾讯批量查询，并发11路（111批→~11轮）"""
    batches = [codes[i:i+50] for i in range(0, len(codes), 50)]
    sem = asyncio.Semaphore(concurrency)
    result = []

    async def fetch_one(batch):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                    url = 'https://qt.gtimg.cn/q=' + ','.join(batch)
                    resp = await client.get(url)
                    return [r for r in (_parse_tencent_line(l) for l in resp.text.split('\n')) if r]
            except Exception:
                return []

    tasks = [fetch_one(b) for b in batches]
    batch_results = await asyncio.gather(*tasks)
    for br in batch_results:
        result.extend(br)
    return result

async def get_json():
    """A 股实时行情 — 腾讯并发优先"""
    # 腾讯
    try:
        codes = [r['代码'] for r in _to_records(ak.stock_zh_a_spot())]
        rows = await _from_tencent_concurrent(codes)
        return json.dumps(rows, ensure_ascii=False)
    except Exception:
        pass
    # 东财
    try: return _to_json(ak.stock_zh_a_spot_em())
    except Exception: pass
    # 新浪
    try: return _to_json(ak.stock_zh_a_spot())
    except Exception: pass
    return '[]'
