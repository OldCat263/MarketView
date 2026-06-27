"""技术指标 — 纯 Python 实现，不引 pandas/numpy"""
import math


def calc_ma(closes, periods=(5, 10, 20, 60, 120, 250)):
    """简单移动平均
    Returns: {f'MA{p}': [None|float, ...]} 长度始终与输入 closes 一致
    """
    result = {}
    for p in periods:
        vals = []
        total = 0.0
        for i, v in enumerate(closes):
            total += v
            if i >= p:
                total -= closes[i - p]
            vals.append(round(total / p, 4) if i >= p - 1 else None)
        result[f'MA{p}'] = vals
    return result


def calc_boll(closes, period=20, k=2):
    """布林带
    Returns: {'MID': [...], 'UPPER': [...], 'LOWER': [...]}
    MID = SMA(N), UP = MID + K*STDDEV(N), LOW = MID - K*STDDEV(N)
    """
    n = len(closes)
    mid = [None] * n
    upper = [None] * n
    lower = [None] * n

    for i in range(period - 1, n):
        window = closes[i - period + 1: i + 1]
        avg = sum(window) / period
        variance = sum((x - avg) ** 2 for x in window) / period
        std = math.sqrt(variance)
        mid[i] = round(avg, 4)
        upper[i] = round(avg + k * std, 4)
        lower[i] = round(avg - k * std, 4)

    return {'MID': mid, 'UPPER': upper, 'LOWER': lower}


def calc_macd(closes, fast=12, slow=26, signal=9):
    """MACD
    EMA: α=2/(N+1), EMA[0]=close[0], EMA[i]=close*α + prev*(1-α)
    DIF = EMA12 - EMA26
    DEA = EMA9(DIF)
    HIST = (DIF - DEA) * 2
    Returns: {'DIF': [...], 'DEA': [...], 'HIST': [...]}
    """
    n = len(closes)

    def _ema(data, period):
        alpha = 2.0 / (period + 1)
        result = [None] * n
        # 找第一个有效值初始化 EMA
        first = 0
        while first < n and data[first] is None:
            first += 1
        if first >= n:
            return result
        result[first] = data[first]
        for i in range(first + 1, n):
            if data[i] is not None:
                result[i] = data[i] * alpha + result[i - 1] * (1 - alpha)
            else:
                result[i] = result[i - 1]
        return result

    ema12 = _ema(closes, fast)
    ema26 = _ema(closes, slow)
    dif = [None] * n
    for i in range(n):
        if ema12[i] is not None and ema26[i] is not None:
            dif[i] = round(ema12[i] - ema26[i], 4)

    dea = _ema(dif, signal)
    hist = [None] * n
    for i in range(n):
        if dif[i] is not None and dea[i] is not None:
            hist[i] = round((dif[i] - dea[i]) * 2, 4)

    return {'DIF': dif, 'DEA': dea, 'HIST': hist}


# ── V1.9.0 新增因子指标 ──

def calc_rsi(closes, period=14):
    """RSI(14) 相对强弱指标 — 100 - 100/(1+avg_gain/avg_loss)"""
    n = len(closes)
    if n < period + 1:
        return {'RSI': [None] * n}

    gains, losses, rsi = [], [], [None] * n
    for i in range(1, n):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    # Smith 平滑
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, n - 1):
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi[i + 1] = round(100 - 100 / (1 + rs), 2)
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    return {'RSI': rsi}


def calc_atr(highs, lows, closes, period=14):
    """ATR(14) 平均真实波幅"""
    n = len(closes)
    if n < 2:
        return {'ATR': [None] * n}

    tr_list = []
    for i in range(1, n):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        tr_list.append(tr)

    atr = [None] * n
    if len(tr_list) >= period:
        atr_val = sum(tr_list[:period]) / period
        atr[period] = round(atr_val, 4)
        for i in range(period, len(tr_list)):
            atr_val = (atr_val * (period - 1) + tr_list[i]) / period
            atr[i + 1] = round(atr_val, 4)

    return {'ATR': atr}


def calc_vpt(closes, volumes):
    """VPT 量价趋势 — 累积 (close-prev_close)/prev_close * volume"""
    n = len(closes)
    vpt = [None] * n
    cum = 0.0
    for i in range(1, n):
        if closes[i-1] and closes[i-1] != 0:
            cum += (closes[i] - closes[i-1]) / closes[i-1] * volumes[i]
        vpt[i] = round(cum, 2)
    return {'VPT': vpt}
