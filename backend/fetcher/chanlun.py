"""缠论 108 课完整实现 — 纯 Python，零依赖
===========================================
Step 1a (基础层): 包含处理 → 分型 → 笔 → 一类买卖点（简化版）
Step 3.5 (进阶层): 线段 → 中枢 → 走势 → 背驰 → 二三买卖点

参考: chanlun/ 目录（108课原文，只读）

数据结构约定:
  K线行 = [date, open, close, high, low, volume, amount]
  索引:   0     1     2      3     4     5       6

分析结果 dict 键:
  step1a: has_bi, buy_points, sell_points, bi_list, fenxing_list
  step3.5: zhongshu_list, zoushi, beichi_list, buy_points_ext, sell_points_ext
"""

# ============================================================
# Step 1a: 基础层 — 包含处理 → 分型 → 笔 → 一类买卖点
# ============================================================

def _is_up_kline(prev_kl, kl):
    """判断当前K线方向（与前一K线比较）"""
    return kl[2] > prev_kl[2]  # close > prev_close → 向上


def process_inclusions(rows):
    """包含处理: 消除相邻K线的包含关系，返回标准K线列表。
    规则（缠论第 62 课）:
    - 向上序列: 取高高(high=max(a.h,b.h)) 高高(low=max(a.l,b.l))
    - 向下序列: 取低高(high=min(a.h,b.h)) 低低(low=min(a.l,b.l))
    """
    if len(rows) < 2:
        return [list(r) for r in rows]

    result = [list(rows[0])]
    direction = None  # True=向上, False=向下

    for i in range(1, len(rows)):
        curr = list(rows[i])
        prev = result[-1]

        # 判断包含关系: high1>=high2 and low1<=low2 → 前包含后
        #               high1<=high2 and low1>=low2 → 后包含前
        has_inclusion = (prev[3] <= curr[3] and prev[4] >= curr[4]) or \
                        (prev[3] >= curr[3] and prev[4] <= curr[4])

        if not has_inclusion:
            direction = _is_up_kline(prev, curr)
            result.append(curr)
            continue

        # 有包含关系 → 合并
        if direction is None:
            # 前两根K线，用简单规则: 非包含即合并
            direction = _is_up_kline(prev, curr) if prev[2] != curr[2] else True

        if direction:  # 向上 → 取高高
            merged_high = max(prev[3], curr[3])
            merged_low = max(prev[4], curr[4])
        else:  # 向下 → 取低低
            merged_high = min(prev[3], curr[3])
            merged_low = min(prev[4], curr[4])

        # 合并K线: date 取较新的, open/close 按方向取
        result[-1] = [
            curr[0],                           # 用后一根的时间
            prev[1] if direction else curr[1],  # open
            curr[2] if direction else prev[2],  # close
            merged_high,
            merged_low,
            prev[5] + curr[5],                 # volume 累加
            prev[6] + curr[6],                 # amount 累加
        ]

    return result


def _find_fenxing(rows):
    """识别顶分型和底分型（缠论第 63 课）。
    顶分型: 中间K线最高价最高，左右K线最高价较低
    底分型: 中间K线最低价最低，左右K线最低价较高
    Returns: [(index, type, row), ...]  type='top'|'bottom'
    """
    if len(rows) < 3:
        return []

    fx_list = []
    for i in range(1, len(rows) - 1):
        left, mid, right = rows[i-1], rows[i], rows[i+1]

        # 顶分型: mid.h > left.h and mid.h > right.h
        if mid[3] > left[3] and mid[3] > right[3]:
            fx_list.append((i, 'top', mid))

        # 底分型: mid.l < left.l and mid.l < right.l
        if mid[4] < left[4] and mid[4] < right[4]:
            fx_list.append((i, 'bottom', mid))

    return fx_list


def _connect_bi(fx_list):
    """连接笔: 从分型序列中连接顶-底交替的笔（缠论第 65 课）。
    笔的定义: 相邻的顶和底之间至少有一根独立K线（非顶非底）。
    Returns: [(start_idx, end_idx, direction, start_price, end_price), ...]
    """
    if len(fx_list) < 2:
        return []

    bi_list = []
    # 过滤: 连续同类型分型取最极值
    filtered = [fx_list[0]]

    for i in range(1, len(fx_list)):
        curr = fx_list[i]
        prev = filtered[-1]

        if curr[1] == prev[1]:  # 同类型
            if curr[1] == 'top' and curr[2][3] > prev[2][3]:
                filtered[-1] = curr  # 取更高的顶
            elif curr[1] == 'bottom' and curr[2][4] < prev[2][4]:
                filtered[-1] = curr  # 取更低的底
        elif curr[0] - prev[0] >= 1:  # 至少隔 1 根K线（简化: 中间K线≥1）
            filtered.append(curr)
        # 否则跳过（不满足笔的K线数要求）

    if len(filtered) < 2:
        return []

    # 连接笔
    for i in range(1, len(filtered)):
        prev_fx = filtered[i-1]
        curr_fx = filtered[i]

        if prev_fx[1] == curr_fx[1]:
            continue  # 同类型，不连

        # 判断方向: bottom→top = 上升笔, top→bottom = 下降笔
        if prev_fx[1] == 'bottom':  # 底→顶 = 上升笔
            direction = 'up'
            start_price = prev_fx[2][4]   # 底的最低点
            end_price = curr_fx[2][3]      # 顶的最高点
        else:  # 顶→底 = 下降笔
            direction = 'down'
            start_price = prev_fx[2][3]   # 顶的最高点
            end_price = curr_fx[2][4]      # 底的最低点

        bi_list.append({
            'start_idx': prev_fx[0],
            'end_idx': curr_fx[0],
            'direction': direction,
            'start_price': round(start_price, 2),
            'end_price': round(end_price, 2),
            'start_date': _make_date_str(prev_fx[2][0]),
            'end_date': _make_date_str(curr_fx[2][0]),
            'strength': round(abs(end_price - start_price) / abs(start_price) * 100, 2) if start_price else 0,
        })

    return bi_list


def _make_date_str(raw_date):
    """将各种日期格式统一为 YYYY-MM-DD 字符串"""
    if isinstance(raw_date, str):
        if len(raw_date) >= 10:
            return raw_date[:10]
        return raw_date
    return str(raw_date)


def _find_buy_sell_points_v1(bi_list, rows):
    """Step 1a 简化版: 一类买卖点 = 笔端点反转处。
    一类买点: 下降笔的终点（底分型处）→ 预期反转向上
    一类卖点: 上升笔的终点（顶分型处）→ 预期反转向下

    Step 3.5 将替换为背驰确认版本。
    """
    buy_points = []
    sell_points = []

    for bi in bi_list:
        date_str = bi['end_date']
        end_idx = bi['end_idx']

        # 取终点K线价格
        if end_idx < len(rows):
            close = rows[end_idx][2]
        else:
            close = bi['end_price']

        point = {
            'date': date_str if date_str else _make_date_str(rows[end_idx][0] if end_idx < len(rows) else ''),
            'price': round(float(close), 2),
            'type': '一类买' if bi['direction'] == 'down' else '一类卖',
            'reason': '下降笔终点，预期反转' if bi['direction'] == 'down' else '上升笔终点，预期反转',
            'strength': round(bi.get('strength', 0), 2),
        }

        if bi['direction'] == 'down':
            buy_points.append(point)
        else:
            sell_points.append(point)

    return buy_points, sell_points


# ============================================================
# 主分析入口
# ============================================================

def analyze(rows, prev_result=None):
    """缠论完整分析流水线。

    Args:
        rows: K线数据 [[date, open, close, high, low, volume, amount], ...]
        prev_result: 前次分析结果（用于增量更新，暂未使用）

    Returns:
        {
            'status': 'ok',
            'has_bi': bool,
            'buy_points': [...],      # Step 1a 简化一类买点
            'sell_points': [...],     # Step 1a 简化一类卖点
            'bi_list': [...],         # 笔列表
            'fenxing_count': int,     # 分型数量
            # Step 3.5 追加:
            # 'zhongshu_list': [...],
            # 'zoushi': {...},
            # 'beichi_list': [...],
            # 'buy_points_ext': [...],
            # 'sell_points_ext': [...],
        }
    """
    if not rows or len(rows) < 3:
        return {
            'status': 'insufficient_data',
            'has_bi': False,
            'buy_points': [],
            'sell_points': [],
            'bi_list': [],
            'fenxing_count': 0,
        }

    # 1. 包含处理
    clean_rows = process_inclusions(rows)

    if len(clean_rows) < 3:
        return {
            'status': 'insufficient_data_after_merge',
            'has_bi': False,
            'buy_points': [],
            'sell_points': [],
            'bi_list': [],
            'fenxing_count': 0,
        }

    # 2. 分型识别
    fx_list = _find_fenxing(clean_rows)

    # 3. 笔的连接
    bi_list = _connect_bi(fx_list)

    # 4. 买卖点（Step 1a 简化版）
    buy_points, sell_points = _find_buy_sell_points_v1(bi_list, clean_rows)

    # 构建分型数据（用于前端可视化）
    fenxing_data = []
    for idx, f_type, row in fx_list:
        fenxing_data.append({
            'index': idx,
            'type': f_type,
            'date': _make_date_str(row[0]),
            'price': round(row[3] if f_type == 'top' else row[4], 2),
        })

    result = {
        'status': 'ok',
        'has_bi': len(bi_list) > 0,
        'buy_points': buy_points,
        'sell_points': sell_points,
        'bi_list': bi_list,
        'fenxing_list': fenxing_data,
        'fenxing_count': len(fenxing_data),
    }

    # Step 3.5 追加的 key 预置空
    result.update({
        'zhongshu_list': [],
        'zoushi': {'type': 'unknown', 'zhongshu_count': 0},
        'beichi_list': [],
        'buy_points_ext': [],
        'sell_points_ext': [],
    })

    return result
