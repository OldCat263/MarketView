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

  // ─── 交易时段判断（北京时间 UTC+8）───
  function isTradingHours(module) {
    if (module === 'crypto') return true;  // 24×7
    var now = new Date();
    var day = now.getUTCDay();       // 0=Sun, 1=Mon, …
    var h = now.getUTCHours() + 8;   // 北京时间
    if (h >= 24) { h -= 24; day = (day + 1) % 7; }
    if (h < 0) { h += 24; day = (day - 1 + 7) % 7; }
    var isWeekday = day >= 1 && day <= 5;
    if (!isWeekday) return false;
    var m = now.getUTCMinutes();
    var t = h * 100 + m;  // HHMM 格式
    if (module === 'us') {
      // 美股夏令时：周一~五 21:30 ~ 次日 4:00（北京时间）
      return t >= 2130 || t < 400;
    }
    if (module === 'hk') {
      return t >= 930 && t < 1600;
    }
    // stock/etf/index: 周一~五 9:30-15:00
    return t >= 930 && t < 1500;
  }

  // ─── 前缀推断：spot 代码（无前缀）→ K-line API 代码（有前缀）───
  function inferCode(module, spotCode) {
    if (!spotCode) return spotCode;
    if (module === 'hk') return 'hk' + spotCode;
    if (module === 'us') return 'us' + spotCode;
    if (module === 'crypto') return spotCode.indexOf('USDT') >= 0 ? spotCode : spotCode + 'USDT';
    // stock/etf/index: 首字符 0/2/3 → sz，否则 sh
    var first = spotCode.charAt(0);
    var prefix = (first === '0' || first === '2' || first === '3') ? 'sz' : 'sh';
    return prefix + spotCode;
  }

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
        formatter: function(params) {
          if (!params || !params.length) return '';
          var date = params[0].axisValue;
          var html = '<div style="font-weight:600;margin-bottom:5px;color:' + C.gold + '">' + date + '</div>';
          for (var i = 0; i < params.length; i++) {
            var p = params[i];
            var sn = p.seriesName;
            var v = p.value;
            var mk = p.marker;
            if (sn === 'K线') {
              // v = [open, close, low, high]
              html += mk + ' <b>K线</b><br/>';
              html += '&nbsp;&nbsp;开盘: ' + (v[0] != null ? v[0].toFixed(2) : '-') + '<br/>';
              html += '&nbsp;&nbsp;收盘: ' + (v[1] != null ? v[1].toFixed(2) : '-') + '<br/>';
              html += '&nbsp;&nbsp;最高: ' + (v[3] != null ? v[3].toFixed(2) : '-') + '<br/>';
              html += '&nbsp;&nbsp;最低: ' + (v[2] != null ? v[2].toFixed(2) : '-') + '<br/>';
            } else if (sn.indexOf('MACD') === 0) {
              // MACD 系列在一行显示
              if (i === 0 || params[i-1].seriesName.indexOf('MACD') !== 0) {
                var difV = '-', deaV = '-', histV = '-';
                for (var j = i; j < params.length; j++) {
                  var pj = params[j];
                  if (pj.seriesName === 'MACD快线') difV = (pj.value != null ? pj.value.toFixed(4) : '不足');
                  if (pj.seriesName === 'MACD慢线') deaV = (pj.value != null ? pj.value.toFixed(4) : '不足');
                  if (pj.seriesName === 'MACD柱') histV = (pj.value != null ? pj.value.toFixed(4) : '不足');
                }
                html += mk + ' <b>MACD</b>&nbsp; DIF:' + difV + ' / DEA:' + deaV + ' / HIST:' + histV + '<br/>';
              }
            } else {
              var label = v != null ? (typeof v === 'number' ? v.toFixed(2) : v) : '数据不足';
              html += mk + ' ' + sn + ': ' + label + '<br/>';
            }
          }
          return html;
        },
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
      { key: 'MA5',   name: 'MA5(5日)',     color: C.ma5,   lineWidth: 1 },
      { key: 'MA10',  name: 'MA10(10日)',   color: C.ma10,  lineWidth: 1 },
      { key: 'MA20',  name: 'MA20(20日)',   color: C.ma20,  lineWidth: 1 },
      { key: 'MA60',  name: 'MA60(60日)',   color: C.ma60,  lineWidth: 1 },
      { key: 'MA120', name: 'MA120(半年)',  color: C.ma120, lineWidth: 1 },
      { key: 'MA250', name: 'MA250(年线)',  color: C.ma250, lineWidth: 1 },
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
        name: '布林上轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.UPPER, symbol: 'none',
        lineStyle: { color: C.bollUp, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }
    if (boll.MID && boll.MID.length) {
      series.push({
        name: '布林中轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.MID, symbol: 'none',
        lineStyle: { color: C.bollMid, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }
    if (boll.LOWER && boll.LOWER.length) {
      series.push({
        name: '布林下轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: boll.LOWER, symbol: 'none',
        lineStyle: { color: C.bollLow, width: 0.8, type: 'dashed', opacity: 0.5 },
      });
    }

    // ── VOL 副图：成交量柱 ──
    var volXIdx = showMACD ? 1 : 1;
    var volYIdx = showMACD ? 1 : 1;
    series.push({
      name: '成交量', type: 'bar', xAxisIndex: volXIdx, yAxisIndex: volYIdx,
      data: volumes.map(function(v, i) {
        return { value: v, itemStyle: { color: volColors[i] } };
      }),
    });

    // ── MACD 副图（仅 showMACD 时）──
    if (showMACD) {
      if (macd.DIF && macd.DIF.length) {
        series.push({
          name: 'MACD快线', type: 'line', xAxisIndex: 2, yAxisIndex: 2,
          data: macd.DIF, symbol: 'none',
          lineStyle: { color: C.dif, width: 1 },
        });
      }
      if (macd.DEA && macd.DEA.length) {
        series.push({
          name: 'MACD慢线', type: 'line', xAxisIndex: 2, yAxisIndex: 2,
          data: macd.DEA, symbol: 'none',
          lineStyle: { color: C.dea, width: 1 },
        });
      }
      if (macdHist.length) {
        series.push({
          name: 'MACD柱', type: 'bar', xAxisIndex: 2, yAxisIndex: 2,
          data: macdHist.map(function(v, i) {
            return { value: v, itemStyle: { color: histColors[i] } };
          }),
        });
      }
    }

    return series;
  }

  // ─── 加载数据 ───
  // force=true 时跳过缓存（手动切周期/代码）
  // module + code 参数化：code 可选，无则从 KL_NAMES 取默认
  async function loadData(module, code, force) {
    if (!module) module = currentModule;
    if (!code) {
      var def = KL_NAMES[module];
      if (!def) return;
      code = def.code;
    } else {
      // 推断前缀（spot 代码可能无前缀）
      code = inferCode(module, code);
    }
    currentModule = module;
    var cacheKey = 'kl_' + module + '_' + code + '_' + currentPeriod;

    // ── 读缓存 ──
    if (!force) {
      try {
        var raw = sessionStorage.getItem('mv_' + cacheKey);
        if (raw) {
          var cached = JSON.parse(raw);
          var age = Date.now() - cached.ts;
          var maxAge = isTradingHours(module) ? 60000 : Infinity;
          if (age < maxAge) {
            lastResp = cached.data;
            document.getElementById('klineTitle').textContent = (cached.data.name || code) + ' (' + code + ')';
            render(cached.data);
            return;
          }
        }
      } catch(e) {}
    }

    // ── fetch 数据 ──
    var url = MV.API + '/api/kline/' + module + '/' + code +
              '?period=' + currentPeriod + '&count=750';
    try {
      var resp = await fetch(url).then(function(r) { return r.json(); });
      if (resp.error) { console.warn('Kline load error:', resp.error); return; }
      lastResp = resp;
      var displayName = resp.name || code;
      document.getElementById('klineTitle').textContent = displayName + ' (' + code + ')';
      MV.cacheSet(cacheKey, resp);
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
  function show(module, code) {
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
    // 清空搜索框
    var ks = document.getElementById('klineSearch');
    if (ks) ks.value = code || '';
    // 隐藏下拉
    hideSuggest();
    // 初始化图表 + 加载数据
    if (!chart) initChart();
    loadData(currentModule, code);
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
    loadData(currentModule, null, true);  // 手动切周期 → 跳过缓存
  }

  // ─── 搜索：构建代码索引 ───
  function buildCodeIndex() {
    var index = [];
    var seen = {};
    MODULE_ORDER.forEach(function(m) {
      var cached = MV.cacheGet(m, true);
      if (cached && cached.rows) {
        cached.rows.forEach(function(row) {
          var cd = row['代码'] || row['交易对'];
          if (!cd || seen[cd]) return;
          seen[cd] = true;
          index.push({
            code: cd,
            name: row['名称'] || row['名称'] || cd,
            module: m,
          });
        });
      }
    });
    if (index.length === 0) {
      // fallback: 至少包含默认代码
      MODULE_ORDER.forEach(function(m) {
        var info = KL_NAMES[m];
        if (info) index.push({code: info.code, name: info.name, module: m});
      });
    }
    return index;
  }

  // ─── 搜索输入 ───
  function onSearchInput() {
    var input = document.getElementById('klineSearch');
    var sug = document.getElementById('klineSuggest');
    if (!input || !sug) return;
    var q = input.value.trim().toLowerCase();
    if (q.length < 1) { sug.style.display = 'none'; return; }
    var index = buildCodeIndex();
    // 当前模块优先
    index.sort(function(a, b) {
      if (a.module === currentModule && b.module !== currentModule) return -1;
      if (b.module === currentModule && a.module !== currentModule) return 1;
      return 0;
    });
    var matches = [];
    for (var i = 0; i < index.length && matches.length < 10; i++) {
      var item = index[i];
      if (item.code.toLowerCase().indexOf(q) >= 0 || item.name.toLowerCase().indexOf(q) >= 0) {
        matches.push(item);
      }
    }
    if (matches.length === 0) { sug.style.display = 'none'; return; }
    var html = '';
    matches.forEach(function(item) {
      html += '<div class="kline-suggest-item" data-code="' + item.code +
        '" data-module="' + item.module + '" data-name="' + item.name +
        '" onclick="MV.Kline.selectCode(this)" onmouseenter="MV.Kline.highlightItem(this)">' +
        '<span>' + item.name + '</span>' +
        '<span class="ks-code">' + item.code + '</span></div>';
    });
    sug.innerHTML = html;
    sug.style.display = 'block';
  }

  // ─── 选中建议项 ───
  function selectCode(el) {
    var module = el.getAttribute('data-module');
    var code = el.getAttribute('data-code');
    var name = el.getAttribute('data-name');
    var input = document.getElementById('klineSearch');
    if (input) input.value = name + ' (' + code + ')';
    hideSuggest();
    currentModule = module;
    loadData(module, code, true);
  }

  // ─── 高亮建议项 ───
  function highlightItem(el) {
    var items = document.querySelectorAll('.kline-suggest-item');
    for (var i = 0; i < items.length; i++) { items[i].classList.remove('active'); }
    el.classList.add('active');
  }

  // ─── 隐藏下拉 ───
  function hideSuggest() {
    var sug = document.getElementById('klineSuggest');
    if (sug) sug.style.display = 'none';
  }

  // ─── 公开 API ───
  return {
    show: show,
    _hide: _hide,
    toggleMACD: toggleMACD,
    switchPeriod: switchPeriod,
    onSearchInput: onSearchInput,
    selectCode: selectCode,
    highlightItem: highlightItem,
    getModule: function() { return currentModule; },
  };
})();

// ─── 图表区点击 → 隐藏搜索下拉 ───
document.addEventListener('DOMContentLoaded', function() {
  var chartWrap = document.getElementById('kline-chart');
  if (chartWrap) {
    chartWrap.addEventListener('click', function() {
      var sug = document.getElementById('klineSuggest');
      if (sug) sug.style.display = 'none';
    });
  }
});

// ─── 搜索框回车 → 选第一个建议 ───
document.addEventListener('DOMContentLoaded', function() {
  var ks = document.getElementById('klineSearch');
  if (ks) {
    ks.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        var first = document.querySelector('.kline-suggest-item');
        if (first) MV.Kline.selectCode(first);
      }
    });
  }
});

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

MV.goKline = function(module, code) {
  MV.Kline.show(module || 'stock', code);
};
