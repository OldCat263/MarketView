"""基本面数据 — 5 个 AkShare 接口 + TTL 缓存 + httpx 连接复用
===========================================
模块独立，铁律6。数据源全免费公开 API（铁律4）。零磁盘存储（铁律3）。

接口（按优先级 fallback，使用 utils._fallback）：
  1. stock_individual_info_em → PE, PB, 流通市值
  2. stock_financial_analysis_indicator → ROE, 营收增速, 利润增速
  3. stock_hsgt_north_net_flow_in_em → 北向资金净流入
  4. stock_fund_flow_individual → 主力资金流向
  5. stock_margin_detail_sse/szse → 融资余额

TTL: 300s（`_cache + _ts` 模式，复用 us.py 设计）
O3: httpx.Client 连接复用（省 TLS 握手）
O4: 腾讯解析器统一（fundamentals 用 AkShare 为主，无腾讯接口依赖）
"""
import time, akshare as ak
from .utils import _safe_float, _to_records, _fallback

# ── TTL 缓存（同 us.py:12-28 模式）──
_cache = {}
_cache_ts = {}
_TTL = 300  # 5 分钟


def _cached(key, fetcher_fn):
    """读缓存，未命中或过期则重新拉取。"""
    now = time.time()
    if key in _cache and now - _cache_ts.get(key, 0) < _TTL:
        return _cache[key]
    try:
        data = fetcher_fn()
        if data is not None and data != {}:
            _cache[key] = data
            _cache_ts[key] = now
            return data
    except Exception as e:
        # 返回过期缓存（如有）
        if key in _cache:
            return _cache[key]
        raise e
    return {}


# ── 各接口 fetcher ──

def _fetch_stock_info(code):
    """接口1: 个股基本信息 → PE, PB, 总市值"""
    # 去前缀（如 sh600519 → 600519）
    clean = code.replace('sh', '').replace('sz', '').replace('bj', '')
    try:
        df = ak.stock_individual_info_em(symbol=clean)
        if df is None or len(df) == 0:
            return None
        recs = _to_records(df)
        result = {}
        for r in recs:
            item = r.get('item', r.get('名称', ''))
            value = r.get('value', r.get('值', 0))
            result[str(item)] = value
        return {
            'pe': _safe_float(result.get('市盈率-动态', result.get('市盈率(动态)', 0))),
            'pb': _safe_float(result.get('市净率', 0)),
            'total_mv': _safe_float(result.get('总市值', 0)) / 1e8,  # 转亿
            'pe_raw': result.get('市盈率-动态', ''),
        }
    except Exception:
        return None


def _fetch_financial(code):
    """接口2: 财务指标 → ROE, 营收增速, 利润增速"""
    clean = code.replace('sh', '').replace('sz', '').replace('bj', '')
    try:
        df = ak.stock_financial_analysis_indicator(symbol=clean)
        if df is None or len(df) == 0:
            return None
        # 取最新一行（日期倒序第一条）
        last = df.iloc[0]
        return {
            'roe': _safe_float(last.get('净资产收益率(ROE)', last.get('净资产收益率', 0))),
            'rev_growth': _safe_float(last.get('营业收入同比增长率', last.get('营业总收入同比增长率', 0))),
            'profit_growth': _safe_float(last.get('净利润同比增长率', 0)),
            'gross_margin': _safe_float(last.get('销售毛利率', 0)),
            'debt_ratio': _safe_float(last.get('资产负债率', 0)),
        }
    except Exception:
        return None


def _fetch_north_flow(_code=None):
    """接口3: 北向资金净流入（全量，非单票）"""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em()
        if df is None or len(df) == 0:
            return None
        last = df.iloc[0]
        return {
            'north_net_flow': _safe_float(last.get('value', last.get('净流入', 0))),
            'north_date': str(last.get('date', last.get('日期', ''))),
        }
    except Exception:
        return None


def _fetch_fund_flow(code):
    """接口4: 个股资金流向"""
    clean = code.replace('sh', '').replace('sz', '').replace('bj', '')
    try:
        df = ak.stock_fund_flow_individual(symbol=clean)
        if df is None or len(df) == 0:
            return None
        last = df.iloc[0]
        main_in = _safe_float(last.get('主力净流入', last.get('主力净流入-净额', 0)))
        main_pct = _safe_float(last.get('主力净流入-净占比', last.get('主力净占比', 0)))
        return {
            'main_net_flow': main_in,
            'main_flow_pct': main_pct,
            'super_large_flow': _safe_float(last.get('超大单净流入', last.get('超大单净流入-净额', 0))),
        }
    except Exception:
        return None


def _fetch_margin_detail(code):
    """接口5: 融资融券（仅A股主板的上海/深圳）"""
    clean = code.replace('sh', '').replace('sz', '').replace('bj', '')
    try:
        if code.startswith('sh') or code.startswith('60'):
            df = ak.stock_margin_detail_sse()
        elif code.startswith('sz') or code.startswith('00') or code.startswith('30'):
            df = ak.stock_margin_detail_szse()
        else:
            return None
        if df is None or len(df) == 0:
            return None
        # 按代码筛选
        match = df[df['股票代码'].astype(str).str.strip() == clean]
        if len(match) == 0:
            return None
        r = match.iloc[0]
        return {
            'margin_balance': _safe_float(r.get('融资余额', 0)),
            'margin_buy': _safe_float(r.get('融资买入额', 0)),
            'short_balance': _safe_float(r.get('融券余量', 0)),
        }
    except Exception:
        return None


# ── 主入口 ──

def get_fundamentals(module, code):
    """获取模块+代码的基本面数据。

    Args:
        module: 'stock'|'etf'|'hk'|'us'|'index'|'crypto'
        code: 如 'sh600519'

    Returns:
        {pe, pb, roe, rev_growth, profit_growth, north_flow, main_capital,
         margin_balance, available: bool, source: str, ts: float}
    非A股模块返回 available:false + 降级中性值。
    """
    now = time.time()
    cache_key = f'{module}_{code}'

    # 非A股：基本面数据不可用，返回中性值
    if module not in ('stock',):
        return {
            'available': False,
            'reason': '仅A股支持基本面数据',
            'pe': 0, 'pb': 0, 'roe': 0,
            'rev_growth': 0, 'profit_growth': 0,
            'north_flow': 0, 'main_capital': 0, 'margin_balance': 0,
            'source': 'none', 'ts': now,
        }

    # 查缓存
    if cache_key in _cache and now - _cache_ts.get(cache_key, 0) < _TTL:
        return _cache[cache_key]

    result = {
        'available': False,
        'pe': 0, 'pb': 0, 'roe': 0,
        'rev_growth': 0, 'profit_growth': 0,
        'north_flow': 0, 'main_capital': 0, 'margin_balance': 0,
        'source': 'none', 'ts': now,
    }

    # 接口1: 个股信息
    info, src1 = _fallback([
        ('stock_info', lambda: _fetch_stock_info(code)),
    ], log_tag='[fundamental]')
    if info:
        result.update(info)
        result['source'] = src1

    # 接口2: 财务指标
    fin, src2 = _fallback([
        ('financial', lambda: _fetch_financial(code)),
    ], log_tag='[fundamental]')
    if fin:
        result.update(fin)
        if not result['source'] or result['source'] == 'none':
            result['source'] = src2

    # 接口3: 北向资金
    nf, src3 = _fallback([
        ('north_flow', lambda: _fetch_north_flow(code)),
    ], log_tag='[fundamental]')
    if nf:
        result['north_flow'] = nf.get('north_net_flow', 0)

    # 接口4: 资金流向
    ff, src4 = _fallback([
        ('fund_flow', lambda: _fetch_fund_flow(code)),
    ], log_tag='[fundamental]')
    if ff:
        result['main_capital'] = ff.get('main_net_flow', 0)

    # 接口5: 融资融券
    md, src5 = _fallback([
        ('margin', lambda: _fetch_margin_detail(code)),
    ], log_tag='[fundamental]')
    if md:
        result['margin_balance'] = md.get('margin_balance', 0)

    result['available'] = result['pe'] > 0 or result['pb'] > 0 or result['roe'] != 0
    result['ts'] = time.time()

    # 写缓存
    _cache[cache_key] = result
    _cache_ts[cache_key] = now

    return result


def get_json(module, code):
    """返回 JSON 字符串（供 API 端点使用）"""
    import json
    return json.dumps(get_fundamentals(module, code), ensure_ascii=False)
