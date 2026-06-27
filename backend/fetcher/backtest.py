"""回测系统 — 买卖点配对 → 模拟交易 → 9 指标分组统计
===========================================
纯 Python，零依赖。按信号类型分组统计，不预测方向，只展示历史表现。

9 指标: 胜率/平均收益/盈亏比/夏普比率/最大回撤/连亏次数/盈利因子/持有天数/样本量
"""
import math, time


def _match_trades(buy_points, sell_points, rows):
    """将买卖点配对为交易记录。按时间顺序，买→卖→买→卖交替配对。
    Args:
        buy_points: [{'date','price','type','reason'},...]
        sell_points: [{'date','price','type','reason'},...]
        rows: K线数据（用于查找日期索引）
    Returns:
        [{'entry_date','exit_date','entry_price','exit_price','signal_type','return_pct','hold_days'},...]
    """
    # 合并买卖点按日期排序
    events = []
    for bp in buy_points:
        events.append({'date': str(bp.get('date', '')), 'price': bp.get('price', 0),
                       'side': 'buy', 'type': bp.get('type', '')})
    for sp in sell_points:
        events.append({'date': str(sp.get('date', '')), 'price': sp.get('price', 0),
                       'side': 'sell', 'type': sp.get('type', '一类卖')})

    events.sort(key=lambda e: e['date'])

    trades = []
    pending_buy = None

    for evt in events:
        if evt['side'] == 'buy' and pending_buy is None:
            pending_buy = evt
        elif evt['side'] == 'sell' and pending_buy is not None:
            entry = pending_buy
            exit_ = evt
            ret = (exit_['price'] - entry['price']) / entry['price'] * 100 if entry['price'] else 0

            # 计算持有天数
            hold_days = 1
            try:
                # 从 rows 中找日期索引差
                entry_date = str(entry['date'])[:10]
                exit_date = str(exit_['date'])[:10]
                # 简化: 按 rows 索引估算
                for i, r in enumerate(rows):
                    if str(r[0])[:10] == exit_date:
                        # 倒推找 entry
                        for j in range(i, -1, -1):
                            if str(rows[j][0])[:10] == entry_date:
                                hold_days = i - j + 1
                                break
                        break
            except Exception:
                pass

            trades.append({
                'entry_date': entry['date'],
                'exit_date': exit_['date'],
                'entry_price': round(entry['price'], 2),
                'exit_price': round(exit_['price'], 2),
                'signal_type': entry.get('type', ''),
                'return_pct': round(ret, 2),
                'hold_days': hold_days,
                'win': ret > 0,
            })
            pending_buy = None

    return trades


def _calc_sharpe(returns_pct, risk_free=2.0):
    """夏普比率: (平均年化收益 - 无风险利率) / 年化波动率"""
    if len(returns_pct) < 2:
        return 0.0
    avg = sum(returns_pct) / len(returns_pct)
    variance = sum((r - avg) ** 2 for r in returns_pct) / (len(returns_pct) - 1)
    std = math.sqrt(variance) if variance > 0 else 1e-10
    # 年化（假设每次交易独立，简化处理）
    return round((avg - risk_free / 252) / std, 4) if std > 1e-9 else 0.0


def _calc_max_drawdown(returns_pct):
    """最大回撤（百分比）"""
    if not returns_pct:
        return 0.0
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in returns_pct:
        cum += r
        peak = max(peak, cum)
        dd = (peak - cum)
        max_dd = max(max_dd, dd)
    return round(max_dd, 2)


def _calc_max_consecutive_loss(wins):
    """最大连续亏损次数"""
    max_c = 0
    cur = 0
    for w in wins:
        if not w:
            cur += 1
            max_c = max(max_c, cur)
        else:
            cur = 0
    return max_c


def backtest(chanlun_result, rows):
    """对缠论分析结果进行历史回测。

    Args:
        chanlun_result: analyze() 返回的 dict（含 buy_points/sell_points）
        rows: K线数据

    Returns:
        {'trades': [...], 'stats': {'一类买':{...}, '一类卖':{...}, 'all':{...}},
         'summary': str, 'ts': float}
    每组统计含 9 项指标。
    """
    buy_pts = chanlun_result.get('buy_points', [])
    sell_pts = chanlun_result.get('sell_points', [])

    trades = _match_trades(buy_pts, sell_pts, rows)

    # 按信号类型分组
    groups = {}
    for t in trades:
        sig = t['signal_type']
        if sig not in groups:
            groups[sig] = []
        groups[sig].append(t)
    groups['all'] = trades

    stats = {}
    summary_parts = []

    for sig, group_trades in groups.items():
        if not group_trades:
            continue

        n = len(group_trades)
        wins = [t['win'] for t in group_trades]
        rets = [t['return_pct'] for t in group_trades]
        win_count = sum(wins)
        loss_count = n - win_count

        win_rate = round(win_count / n * 100, 1) if n > 0 else 0
        avg_return = round(sum(rets) / n, 2) if n > 0 else 0
        avg_win = round(sum(r for r in rets if r > 0) / max(win_count, 1), 2)
        avg_loss = round(sum(r for r in rets if r <= 0) / max(loss_count, 1), 2)
        pl_ratio = round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
        sharpe = _calc_sharpe(rets)
        max_dd = _calc_max_drawdown(rets)
        max_cl = _calc_max_consecutive_loss(wins)

        # 盈利因子
        gross_profit = sum(r for r in rets if r > 0)
        gross_loss = abs(sum(r for r in rets if r <= 0))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        # 持有天数
        hold_days = [t['hold_days'] for t in group_trades]
        hold_avg = round(sum(hold_days) / n, 1) if n > 0 else 0
        sorted_holds = sorted(hold_days)
        hold_med = sorted_holds[n // 2] if n > 0 else 0

        stats[sig] = {
            'sample_count': n,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'pl_ratio': pl_ratio,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'max_consec_loss': max_cl,
            'profit_factor': profit_factor,
            'hold_avg': hold_avg,
            'hold_med': hold_med,
        }

        if sig != 'all':
            summary_parts.append(
                f"{sig}: 胜率{win_rate}%({n}笔) 盈亏比{pl_ratio} "
                f"夏普{sharpe} 最大回撤{max_dd}%"
            )

    return {
        'trades': trades,
        'stats': stats,
        'summary': ' | '.join(summary_parts) if summary_parts else '无交易信号',
        'ts': time.time(),
    }
