/**
 * MarketView K线模块 — V1.7.0 Step 3
 * ECharts 5 三联图（主图+VOL+MACD）+ 导航显隐 + 周期切换
 * 命名空间 MV.Kline，不碰 ST / _sse
 */
window.MV.Kline = (function() {
  // ─── 默认代码表（与 backend/main.py KL_NAMES 同步）───
  var KL_NAMES = {
    stock:   {code: 'sh600519', name: '贵州茅台'},
    etf:     {code: 'sh510300', name: '沪深300ETF'},
    hk:      {code: 'hk00700', name: '腾讯控股'},
    us:      {code: 'usAAPL',   name: '苹果'},
    index:   {code: 'sh000001', name: '上证指数'},
    crypto:  {code: 'BTCUSDT',  name: 'BTC/USDT'},
  };
  var MODULE_ORDER = ['stock','etf','hk','us','index','crypto'];
  var PERIODS = ['1m','5m','15m','30m','60m','1d','1w','1M'];

  // ─── 色值（项目 :root 变量 + MA 配色表）───
  var C = {
    bg:     '#0f1117',
    card:   '#1a1d27',
    border: '#2a2d37',
    text:   '#d1d4dc',
    dim:    '#787b86',
    up:     '#ef4444',   // 红涨
    down:   '#22c55e',   // 绿跌
    gold:   '#f59e0b',
    // MA 配色（附录 MA 配色表）
    ma5:    '#f59e0b',   // gold
    ma10:   '#3b82f6',   // blue
    ma20:   '#8b5cf6',   // purple
    ma60:   '#06b6d4',   // cyan
    ma120:  '#22c55e',   // green
    ma250:  '#ef4444',   // red
    // BOLL
    bollUp: '#787b86',
    bollMid:'#f59e0b',
    bollLow:'#787b86',
    // MACD
    dif:    '#f59e0b',   // gold
    dea:    '#3b82f6',   // blue
  };

  // ─── 内部状态 ───
  var chart = null;
  var currentModule = 'stock';
  var currentPeriod = '1d';
  var showMACD = false;      // MACD 默认关
  var lastResp = null;       // 缓存最近一次响应（MACD 切换时重渲染）
  var _resizeHandler = null;

  // ─── 数据转换：API [date, open, close, high, low, vol, amt] → ECharts candlestick [o, c, l, h] ───
  function toCandlestick(rows) {
    var result = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      result.push([r[1], r[2], r[4], r[3]]); // [open, close, low, high]
    }
    return result;
  }

  // ─── 构建 ECharts Option ───
  function buildOption(resp) {
    var dates = resp.data.map(function(r) { return r[0]; });
    var ohlc = toCandlestick(resp.data);
    var volumes = resp.data.map(function(r) { return r[5]; });
    var ma = resp.ma || {};
    var boll = resp.boll || {};
    var macd = resp.macd || {};

    // 涨跌染色
    var volColors = resp.data.map(function(r) {
      return r[2] >= r[1] ? C.up : C.down;  // close >= open → 红涨
    });

    // MACD HIST 涨跌染色
    var macdHist = macd.HIST || [];
    var histColors = macdHist.map(function(v) {
      return v >= 0 ? C.up : C.down;
    });

    // ─── 基础轴配置 ───
    var baseAxisLabel = { color: C.dim, fontSize: 11 };
    var baseSplitLine = { lineStyle: { color: C.border, type: 'dashed', opacity: 0.3 } };

    var option = {
      backgroundColor: C.bg,
      color: [C.up, C.down],
      animation: true,
      animationDuration: 300,

      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: C.card,
        borderColor: C.border,
        textStyle: { color: C.text, fontSize: 12 },
      },

      axisPointer: {
        link: [{ xAxisIndex: 'all' }],
      },

      // === MACD 关闭时 2 面板 / 开启时 3 面板 ===
      grid: showMACD ? [
        { left: '8%', right: '2%', top: '5%', height: '52%' },
        { left: '8%', right: '2%', top: '63%', height: '12%' },
        { left: '8%', right: '2%', top: '78%', height: '17%' },
      ] : [
        { left: '8%', right: '2%', top: '5%', height: '68%' },
        { left: '8%', right: '2%', top: '78%', height: '17%' },
      ],

      xAxis: showMACD ? [
        { gridIndex: 0, type: 'category', data: dates, axisLabel: baseAxisLabel,
          axisLine: { lineStyle: { color: C.border } },
          axisTick: { show: false }, splitLine: { show: false } },
        { gridIndex: 1, type: 'category', data: dates, axisLabel: { show: false },
          axisTick: { show: false }, splitLine: { show: false } },
        { gridIndex: 2, type: 'category', data: dates, axisLabel: baseAxisLabel,
          axisLine: { lineStyle: { color: C.border } },
          axisTick: { show: false }, splitLine: { show: false } },
      ] : [
        { gridIndex: 0, type: 'category', data: dates, axisLabel: baseAxisLabel,
          axisLine: { lineStyle: { color: C.border } },
          axisTick: { show: false }, splitLine: { show: false } },
        { gridIndex: 1, type: 'category', data: dates, axisLabel: baseAxisLabel,
          axisLine: { lineStyle: { color: C.border } },
          axisTick: { show: false }, splitLine: { show: false } },
      ],

      yAxis: showMACD ? [
        { gridIndex: 0, scale: true, splitLine: baseSplitLine,
          axisLabel: baseAxisLabel, position: 'left' },
        { gridIndex: 1, scale: true, splitLine: { show: false },
          axisLabel: { color: C.dim, fontSize: 10 }, position: 'left' },
        { gridIndex: 2, scale: true, splitLine: baseSplitLine,
          axisLabel: baseAxisLabel, position: 'left' },
      ] : [
        { gridIndex: 0, scale: true, splitLine: baseSplitLine,
          axisLabel: baseAxisLabel, position: 'left' },
        { gridIndex: 1, scale: true, splitLine: { show: false },
          axisLabel: { color: C.dim, fontSize: 10 }, position: 'left' },
      ],

      dataZoom: [
        { type: 'inside', xAxisIndex: showMACD ? [0,1,2] : [0,1], start: 50, end: 100 },
        { type: 'slider', xAxisIndex: showMACD ? [0,1,2] : [0,1], start: 50, end: 100,
          height: 20, bottom: 2, borderColor: C.border,
          backgroundColor: C.card, fillerColor: 'rgba(245,158,11,.15)',
          handleStyle: { color: C.gold }, textStyle: { color: C.dim, fontSize: 10 } },
      ],

      series: buildSeries(ohlc, volumes, volColors, ma, boll, macd, macdHist, histColors),
    };

    return option;
  }

  function buildSeries(ohlc, volumes, volColors, ma, boll, macd, macdHist, histColors) {
    var series = [];

    // ── 主图：K线 ──
    series.push({
      name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0,
      data: ohlc,
      itemStyle: {
        color: C.up, color0: C.down,
        borderColor: C.up, borderColor0: C.down,
      },
      markPoint: { show: false },
    });

    // ── 主图：MA 线 ──
    var maDefs = [
      { key: 'MA5',   name: 'MA5',   color: C.ma5,   lineWidth: 1 },
      { key: 'MA10',  name: 'MA10',  color: C.ma10,  lineWidth: 1 },
      { key: 'MA20',  name: 'MA20',  color: C.ma20,  lineWidth: 1 },
      { key: 'MA60',  name: 'MA60',  color: C.ma60,  lineWidth: 1 },
      { key: 'MA120', name: 'MA120', color: C.ma120, lineWidth: 1 },
      { key: 'MA250', name: 'MA250', color: C.ma250, lineWidth: 1 },
    ];
    maDefs.forEach(function(d) {
      if (ma[d.key] && ma[d.key].length) {
        series.push({
          name: d.name, type: 'line', xAxisIndex: 0, yAxisIndex: 0,
          data: ma[d.key],
          symbol: 'none',
          lineStyle: { color: d.color, width: d.lineWidth, opacity: 0.9 },
        });
      }
    });

    // ── 主图：BOLL 线（虚线）──
    if (boll.UPPER && boll.UPPER.length) {
      series.push({
        name: 'BOLL-UP', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.UPPER, symbol: 'none',
        lineStyle: { color: C.bollUp, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }
    if (boll.MID && boll.MID.length) {
      series.push({
        name: 'BOLL-MID', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.MID, symbol: 'none',
        lineStyle: { color: C.bollMid, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }
    if (boll.LOWER && boll.LOWER.length) {
      series.push({
        name: 'BOLL-LOW', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.LOWER, symbol: 'none',
        lineStyle: { color: C.bollLow, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }

    // ── VOL 副图：成交量柱 ──
    var volXIdx = showMACD ? 1 : 1;
    var volYIdx = showMACD ? 1 : 1;
    series.push({
      name: 'VOL', type: 'bar', xAxisIndex: volXIdx, yAxisIndex: volYIdx,
      data: volumes.map(function(v, i) {
        return { value: v, itemStyle: { color: volColors[i] } };
      }),
    });

    // ── MACD 副图（仅 showMACD 时）──
    if (showMACD) {
      if (macd.DIF && macd.DIF.length) {
        series.push({
          name: 'DIF', type: 'line', xAxisIndex: 2, yAxisIndex: 2,
          data: macd.DIF, symbol: 'none',
          lineStyle: { color: C.dif, width: 1 },
        });
      }
      if (macd.DEA && macd.DEA.length) {
        series.push({
          name: 'DEA', type: 'line', xAxisIndex: 2, yAxisIndex: 2,
          data: macd.DEA, symbol: 'none',
          lineStyle: { color: C.dea, width: 1 },
        });
      }
      if (macdHist.length) {
        series.push({
          name: 'HIST', type: 'bar', xAxisIndex: 2, yAxisIndex: 2,
          data: macdHist.map(function(v, i) {
            return { value: v, itemStyle: { color: histColors[i] } };
          }),
        });
      }
    }

    return series;
  }

  // ─── 加载数据 ───
  async function loadData() {
    var info = KL_NAMES[currentModule];
    if (!info) return;
    var url = MV.API + '/api/kline/' + currentModule + '/' + info.code +
              '?period=' + currentPeriod + '&count=750';
    try {
      var resp = await fetch(url).then(function(r) { return r.json(); });
      if (resp.error) { console.warn('Kline load error:', resp.error); return; }
      lastResp = resp;
      document.getElementById('klineTitle').textContent = info.name + ' (' + info.code + ')';
      render(resp);
    } catch (e) {
      console.warn('Kline fetch failed:', e);
    }
  }

  // ─── 渲染图表 ───
  function render(resp) {
    if (!chart) initChart();
    if (!chart) return;
    var option = buildOption(resp);
    chart.setOption(option, { notMerge: true });
  }

  // ─── 初始化 ECharts ───
  function initChart() {
    var dom = document.getElementById('kline-chart');
    if (!dom) return;
    chart = echarts.init(dom);
    // resize 监听
    if (!_resizeHandler) {
      _resizeHandler = function() { if (chart) chart.resize(); };
      window.addEventListener('resize', _resizeHandler);
    }
  }

  // ─── 显隐 ───
  function show(module) {
    if (module) currentModule = module;
    // 显隐矩阵
    document.getElementById('grid').style.display = 'none';
    document.getElementById('panel').style.display = 'none';
    document.getElementById('kline-view').style.display = 'block';
    // 更新导航
    var nh = document.getElementById('navHome');
    var nk = document.getElementById('navKline');
    if (nh) { nh.classList.remove('active'); }
    if (nk) { nk.classList.add('active'); }
    // 更新周期选择
    document.getElementById('klinePeriod').value = currentPeriod;
    // MACD 复选框
    document.getElementById('macdToggle').checked = showMACD;
    // 初始化图表 + 加载数据
    if (!chart) initChart();
    loadData();
  }

  function _hide() {
    if (chart) { chart.dispose(); chart = null; }
    if (_resizeHandler) {
      window.removeEventListener('resize', _resizeHandler);
      _resizeHandler = null;
    }
    document.getElementById('kline-view').style.display = 'none';
  }

  // ─── MACD 切换 ───
  function toggleMACD() {
    showMACD = document.getElementById('macdToggle').checked;
    if (lastResp) render(lastResp);
  }

  // ─── 周期切换 ───
  function switchPeriod() {
    currentPeriod = document.getElementById('klinePeriod').value;
    loadData();
  }

  // ─── 代码切换（P2-3: 下拉选 6 模块默认代码）───
  function switchCode() {
    var sel = document.getElementById('klineCode');
    if (sel && sel.value) {
      currentModule = sel.value;
      loadData();
    }
  }

  // ─── 填充代码下拉 ───
  function populateCodeSelect() {
    var sel = document.getElementById('klineCode');
    if (!sel) return;
    sel.innerHTML = '';
    MODULE_ORDER.forEach(function(m) {
      var info = KL_NAMES[m];
      if (!info) return;
      var opt = document.createElement('option');
      opt.value = m;
      opt.textContent = info.name + ' (' + info.code + ')';
      if (m === currentModule) opt.selected = true;
      sel.appendChild(opt);
    });
  }

  // ─── 初始化 ───
  populateCodeSelect();

  // ─── 公开 API ───
  return {
    show: show,
    _hide: _hide,
    toggleMACD: toggleMACD,
    switchPeriod: switchPeriod,
    switchCode: switchCode,
    getModule: function() { return currentModule; },
  };
})();

// ─── 导航入口（挂到 MV 上）───
MV.goHome = function() {
  MV.Kline._hide();
  document.getElementById('panel').style.display = 'none';
  document.getElementById('grid').style.display = 'grid';
  var nh = document.getElementById('navHome');
  var nk = document.getElementById('navKline');
  if (nh) nh.classList.add('active');
  if (nk) nk.classList.remove('active');
};

MV.goKline = function(module) {
  MV.Kline.show(module || 'stock');
};
