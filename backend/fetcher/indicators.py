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
