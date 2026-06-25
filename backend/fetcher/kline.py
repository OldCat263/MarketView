"""模块七：K线数据 — 腾讯 qt.gtimg.cn（A股/ETF/指数/港股/美股），Binance（加密）
港股 3 源 fallback：tencent hkfqkline → 东财 stock_hk_hist → 新浪 stock_hk_spot
"""
import json, time, httpx

# ── 腾讯 period 映射 ──
_TX_PERIOD = {
    '1m': 'm1', '5m': 'm5', '15m': 'm15', '30m': 'm30',
    '60m': 'm60', '1d': 'day', '1w': 'week', '1M': 'month',
}

# ── Binance period 映射 ──
_BN_PERIOD = {
    '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
    '60m': '1h', '1d': '1d', '1w': '1w', '1M': '1M',
}


def _fetch_tencent(code, period, count):
    """腾讯 K线通用请求（A股/ETF/指数/港股/美股 均用 fqkline 接口）
    Returns: [[date_str, open, close, high, low, volume, amount], ...] 或 []
    """
    tx_p = _TX_PERIOD.get(period, 'day')
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},{tx_p},,,{count},qfq'
    try:
        resp = httpx.get(url, timeout=30)
        data = resp.json()
        if data.get('code') != 0:
            return []
        stock_data = data.get('data', {}).get(code, {})
        if not stock_data:
            return []
        # 找第一个列表类型的 K线数据（day / qfqday / week / month 等）
        raw = None
        for k, v in stock_data.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], list):
                raw = v
                break
        if not raw:
            return []
        # 腾讯返回按日期降序，反转成升序
        raw = raw[:count]
        raw.reverse()
        rows = []
        for item in raw:
            if len(item) >= 6:
                rows.append([
                    item[0],                          # 日期
                    float(item[1]),                   # 开盘
                    float(item[2]),                   # 收盘
                    float(item[3]),                   # 最高
                    float(item[4]),                   # 最低
                    float(item[5]),                   # 成交量
                    float(item[6]) if len(item) > 6 and not isinstance(item[6], dict) else 0,  # 成交额
                ])
        return rows
    except Exception as e:
        print(f'[kline] {code}: {e}')
        return []


def _fetch_binance(symbol, period, count):
    """Binance K线"""
    bn_p = _BN_PERIOD.get(period, '1d')
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={bn_p}&limit={count}'
    try:
        import os
        proxy = os.environ.get('CRYPTO_PROXY')
        client_kwargs = {'timeout': 30}
        if proxy:
            client_kwargs['proxy'] = proxy
        else:
            # 尝试自动扫描代理
            from .crypto import _found_proxy
            if _found_proxy:
                client_kwargs['proxy'] = _found_proxy
        resp = httpx.get(url, **client_kwargs)
        raw = resp.json()
        rows = []
        for item in raw:
            rows.append([
                time.strftime('%Y-%m-%d', time.gmtime(item[0] / 1000)),
                float(item[1]),  # open
                float(item[4]),  # close
                float(item[2]),  # high
                float(item[3]),  # low
                float(item[5]),  # volume
                float(item[7]),  # quote volume (amount)
            ])
        return rows
    except Exception as e:
        print(f'[kline] crypto {symbol}: {e}')
        return []


# ── 6 模块独立函数 ──

def fetch_kline_stock(code, period='1d', count=750):
    """A股 K线 — 腾讯"""
    return _fetch_tencent(code, period, count)


def fetch_kline_etf(code, period='1d', count=750):
    """ETF K线 — 腾讯"""
    return _fetch_tencent(code, period, count)


# ── 港股 K线 3 源 fallback ──

def _fetch_hk_tencent(code, period, count):
    """腾讯 hkfqkline（主源）"""
    return _fetch_tencent(code, period, count)


def _fetch_hk_em(code, period, count):
    """东财 stock_hk_hist（fallback 1）— 仅日/周/月"""
    import akshare as ak
    period_map = {'1d': 'daily', '1w': 'weekly', '1M': 'monthly'}
    ak_period = period_map.get(period)
    if not ak_period:
        return []  # 分钟级不走东财
    df = ak.stock_hk_hist(symbol=code, period=ak_period, adjust='qfq')
    if df is None or len(df) == 0:
        return []
    df = df.tail(count)
    rows = []
    for _, row in df.iterrows():
        rows.append([
            str(row.get('日期', '')),
            float(row.get('开盘', 0)),
            float(row.get('收盘', 0)),
            float(row.get('最高', 0)),
            float(row.get('最低', 0)),
            float(row.get('成交量', 0)),
            float(row.get('成交额', 0)),
        ])
    return rows


def _fetch_hk_sina(code, period, count):
    """新浪 stock_hk_spot（兜底）— 仅返回 1 行当日行情"""
    if period not in ('1d', '1w', '1M'):
        return []  # 分钟级不走新浪
    import akshare as ak
    df = ak.stock_hk_spot()
    if df is None or len(df) == 0:
        return []
    match = df[df['代码'] == code]
    if len(match) == 0:
        return []
    r = match.iloc[0]
    return [[
        time.strftime('%Y-%m-%d'),
        float(r.get('今开', 0) or 0),
        float(r.get('最新价', 0) or 0),
        float(r.get('最高', 0) or 0),
        float(r.get('最低', 0) or 0),
        float(r.get('成交量', 0) or 0),
        float(r.get('成交额', 0) or 0),
    ]]


def fetch_kline_hk(code, period='1d', count=750):
    """港股 K线：腾讯 hkfqkline（主源）→ 东财 stock_hk_hist → 新浪 spot（兜底）"""
    sources = [
        ('tencent', _fetch_hk_tencent),
        ('eastmoney', _fetch_hk_em),
        ('sina', _fetch_hk_sina),
    ]
    for name, fn in sources:
        try:
            data = fn(code, period, count)
            if data and len(data) > 0:
                return data
        except Exception as e:
            print(f'[kline_hk] {name} fallback: {e}')
    return []


def fetch_kline_us(code, period='1d', count=750):
    """美股 K线 — 腾讯（需 .OQ 后缀）"""
    if '.' not in code:
        code = code + '.OQ'
    return _fetch_tencent(code, period, count)


def fetch_kline_index(code, period='1d', count=750):
    """指数 K线 — 腾讯"""
    return _fetch_tencent(code, period, count)


def fetch_kline_crypto(code, period='1d', count=750):
    """加密货币 K线 — Binance"""
    symbol = code if 'USDT' in code else code + 'USDT'
    return _fetch_binance(symbol, period, count)
