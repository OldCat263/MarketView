/**
 * MarketView 核心引擎
 * 模块注册 → 状态管理 → 数据获取 → 渲染 → 缓存
 */
window.MV = (function() {
  const MODULES = [];
  const registry = {};

  function register(cfg) {
    cfg.sortCol = cfg.sortCol || '涨跌幅';
    cfg.postProcess = cfg.postProcess || (r => r);
    cfg.parseResponse = cfg.parseResponse || (resp => resp.data);
    cfg.tabIndent = cfg.tabIndent || false;
    cfg.lazy = cfg.lazy || false;
    cfg.placeholder = cfg.placeholder || false;
    MODULES.push(cfg);
    registry[cfg.id] = cfg;
  }

  // 中文数字格式化
  function formatChinese(v, col) {
    if (typeof v !== 'number') return String(v);
    if (col.includes('涨跌幅') || col.includes('涨跌') || col.includes('振幅') || col.includes('换手率'))
      return v.toFixed(2) + '%';
    if (col.includes('成交额') || col.includes('成交量')) {
      if (Math.abs(v) >= 1e8) return (v / 1e8).toFixed(2) + '亿';
      if (Math.abs(v) >= 1e4) return (v / 1e4).toFixed(2) + '万';
      return v.toFixed(0);
    }
    return v.toFixed(2);
  }

  // ─── 缓存 ───
  function cacheGet(key, noTtl) {
    try {
      let d = JSON.parse(sessionStorage.getItem('mv_' + key));
      if (d && (noTtl || Date.now() - d.ts < 15000)) return d.data;
    } catch (e) {}
    return null;
  }
  function cacheSet(key, data) {
    try { sessionStorage.setItem('mv_' + key, JSON.stringify({ data, ts: Date.now() })); } catch (e) {}
  }

  // ─── 全局状态 ───
  const API = window.location.protocol + '//' + window.location.host;
  let ST = {}, LOADED = {}, tab = '', rows = [], cols = [], page = 1, pageSize = 50;
  let updateTime = '', sortKey = null, sortDir = 1;
  let loadedCount = 0, totalMods = 0, cryptoOK = false;
  let latestUpdate = 0, loadStart = Date.now();
  let firstVisit = !sessionStorage.getItem('mv_visited');

  // ─── 渲染表格 ───
  function render() {
    let r = rows;
    let q = document.getElementById('search').value.trim().toLowerCase();
    if (q) r = r.filter(row => cols.some(k => String(row[k] || '').toLowerCase().includes(q)));
    if (sortKey && cols.includes(sortKey))
      r = [...r].sort((a, b) => { let va = parseFloat(a[sortKey]) || 0, vb = parseFloat(b[sortKey]) || 0; return (va - vb) * sortDir; });
    let total = r.length, tp = Math.ceil(total / pageSize) || 1;
    if (page > tp) page = tp;
    let start = (page - 1) * pageSize, pr = r.slice(start, start + pageSize);
    document.getElementById('count').textContent = total + ' 条';
    document.getElementById('pageInfo').textContent = '第 ' + page + '/' + tp + ' 页';
    document.getElementById('pager').style.display = total > pageSize ? 'flex' : 'none';
    if (!total) { document.getElementById('thead').innerHTML = ''; document.getElementById('tbody').innerHTML = ''; document.getElementById('empty').style.display = 'block'; return; }
    document.getElementById('empty').style.display = 'none';
    document.getElementById('thead').innerHTML = '<tr>' + cols.map(k => '<th onclick="MV.sort(\'' + k + '\')">' + k + (sortKey === k ? (sortDir > 0 ? ' ↑' : ' ↓') : '') + '</th>').join('') + '</tr>';
    let cfg = registry[tab];
    let fmt = cfg ? (cfg.format || formatChinese) : formatChinese;
    let indent = cfg ? cfg.tabIndent : false;
    document.getElementById('tbody').innerHTML = pr.map(row =>
      '<tr>' + cols.map((k, i) => {
        let v = row[k]; if (v == null) v = '-';
        let c = ''; if (typeof v === 'number' && (k.includes('涨跌幅') || k.includes('change'))) c = v > 0 ? 'up' : v < 0 ? 'down' : '';
        let prefix = (i > 0 && indent) ? '\t\t' : '';
        return '<td class="' + c + '" data-code="' + (row['代码'] || row['交易对'] || '') + '" data-field="' + k + '">' + prefix + fmt(v, k) + '</td>';
      }).join('') + '</tr>'
    ).join('');
  }

  function doSort(k) { sortKey === k ? sortDir *= -1 : (sortKey = k, sortDir = -1); page = 1; ST[tab] = { rows, cols, page, sortKey, sortDir, updateTime, search: document.getElementById('search').value }; render(); }

  // ─── 加载模块数据 ───
  async function loadModule(m) {
    let cfg = registry[m];
    if (!cfg || cfg.placeholder) return;
    let resp = await fetch(API + cfg.endpoint).then(r => r.json());
    let nr = cfg.parseResponse(resp);
    let nt = resp.time || '';
    let def = cfg.columns.length ? cfg.columns : (nr.length ? Object.keys(nr[0]) : []);
    nr = nr.map(r => { let o = {}; def.forEach(k => { o[k] = r[k] !== undefined ? r[k] : '-'; }); return o; });
    nr = cfg.postProcess(nr);
    let sc = cfg.sortCol;
    nr.sort((a, b) => (parseFloat(b[sc]) || 0) - (parseFloat(a[sc]) || 0));
    cacheSet(m, { rows: nr, cols: def, time: nt });
    ST[m] = { rows: nr, cols: def, page: 1, sortKey: null, sortDir: 1, updateTime: nt, search: '', fetchTime: Date.now() };
    LOADED[m] = true;
    let card = document.getElementById('card_' + m);
    if (card) { card.querySelector('.card-status .status').textContent = '✅'; card.querySelector('.card-count').textContent = nr.length + ' 条'; }
    return nr;
  }

  // ─── 切换模块 ───
  function openModule(m) {
    if (m === 'crypto' && !cryptoOK) { startCrypto(); return; }
    if (!LOADED[m]) { startModule(m); return; }
    if (tab) ST[tab] = { rows, cols, page, sortKey, sortDir, updateTime, search: document.getElementById('search').value };
    _connectSSE(m);  // 开启SSE实时推送
    let s = ST[m] || { page: 1, sortKey: null, sortDir: 1, updateTime: '', search: '' };
    rows = s.rows || []; cols = s.cols || []; page = s.page || 1;
    sortKey = s.sortKey; sortDir = s.sortDir; updateTime = s.updateTime || '';
    tab = m; document.getElementById('search').value = s.search || '';
    document.getElementById('moduleTitle').textContent = registry[m].icon + ' ' + registry[m].name;
    document.getElementById('viewTime').textContent = '更新 ' + updateTime;
    document.getElementById('grid').style.display = 'none';
    document.getElementById('panel').style.display = 'block';
    render();
  }

  function closePanel() {
    document.getElementById('panel').style.display = 'none';
    document.getElementById('grid').style.display = 'grid';
  }

  async function startModule(m) {
    if (LOADED[m]) { openModule(m); return; }
    let card = document.getElementById('card_' + m);
    if (card) { card.querySelector('.status').textContent = '⌛'; }
    await loadModule(m);
    if (card) { card.querySelector('.status').textContent = '✅'; card.querySelector('.card-count').textContent = ST[m].rows.length + ' 条'; }
    openModule(m);
  }

  async function startCrypto() {
    let c = document.getElementById('card_crypto');
    c.querySelector('.card-status .status').textContent = '⏳'; c.querySelector('.card-count').textContent = '检测代理...';
    let cs = await fetch(API + '/api/crypto/status').then(r => r.json());
    if (!cs.available) {
      cryptoOK = false;
      c.querySelector('.card-status .status').textContent = '🔒'; c.querySelector('.card-count').textContent = '需代理';
      MV.showToast('未检测到网络代理');
      return;
    }
    cryptoOK = true;
    await startModule('crypto');
  }

  // ─── 预加载 ───
  async function preloadAll() {
    if (firstVisit) { sessionStorage.setItem('mv_visited', '1');
      setInterval(() => {
        let n = document.getElementById('firstNotice');
        if (!n || n.style.display === 'none') return;
        n.innerHTML = '🕐 首次加载中，已用时 <strong>' + Math.round((Date.now() - loadStart) / 1000) + '</strong> 秒';
      }, 1000);
    }

    let cc = document.getElementById('card_crypto');
    cc.querySelector('.card-status .status').textContent = '💤'; cc.querySelector('.card-count').textContent = '点击加载';
    let nc = document.getElementById('card_news');
    nc.querySelector('.card-status .status').textContent = '🚧'; nc.querySelector('.card-count').textContent = '即将上线';
    loadedCount++; totalMods = MODULES.length - 1;

    await Promise.all(MODULES.map(async m => {
      if (m.id === 'crypto' || m.id === 'news' || m.placeholder) return;
      let cached = cacheGet(m.id, true);
      if (cached) {
        ST[m.id] = { rows: cached.rows, cols: cached.cols, page: 1, sortKey: null, sortDir: 1, updateTime: cached.time, search: '', fetchTime: Date.now() };
        LOADED[m.id] = true;
        let card = document.getElementById('card_' + m.id);
        card.querySelector('.card-status .status').textContent = '✅'; card.querySelector('.card-count').textContent = cached.rows.length + ' 条';
        loadedCount++; latestUpdate = Date.now();
        let pct = Math.round(loadedCount / totalMods * 100);
        document.getElementById('loadBar').style.width = pct + '%';
        return;
      }
      try {
        await loadModule(m.id);
        loadedCount++; latestUpdate = Date.now();
        let pct = Math.round(loadedCount / totalMods * 100);
        document.getElementById('loadBar').style.width = pct + '%';
        document.getElementById('loadStatus').textContent = '已加载 ' + loadedCount + '/' + totalMods;
         _updateConnStatus(true);
      } catch (e) {
        let card = document.getElementById('card_' + m.id);
        card.querySelector('.card-status .status').textContent = '❌'; card.querySelector('.card-count').textContent = '加载失败';
        _updateConnStatus(false);
      }
    }));

    if (loadedCount >= totalMods) {
      let notice = document.getElementById('firstNotice');
      if (notice) notice.innerHTML = '✅ 加载完成！已用时 <strong>' + Math.round((Date.now() - loadStart) / 1000) + '</strong> 秒';
      setTimeout(() => { if (notice) notice.style.display = 'none'; }, 2000);
    }
  }

  function _updateConnStatus(ok) {
    let dot = document.getElementById('connDot'), st = document.getElementById('connStatus');
    if (dot) { dot.className = 'conn-dot ' + (ok ? 'on' : 'off'); dot.title = ok ? '实时连接中' : '连接失败'; }
    if (st) st.textContent = ok ? '实时' : '离线';
  }

  // ─── SSE 分片推送 + diff 闪动 ───
  let _sse = null;
  function _connectSSE(m) {
    if (_sse) { _sse.close(); _sse = null; }
    let url = API + '/api/stream/' + m;
    _sse = new EventSource(url);
    _sse.onmessage = function(e) {
      try {
        let msg = JSON.parse(e.data);
        if (!msg || !msg.data || !msg.data.length) return;
        let st = ST[m];
        if (!st || !st.rows) return;
        let shardRows = msg.data;
        // 为分片数据建索引，按"代码"匹配旧行做 diff
        let byCode = {};
        shardRows.forEach(r => { let c = r['代码'] || r['交易对']; if (c) byCode[c] = r; });
        let changed = false;
        st.rows.forEach((old, idx) => {
          let code = old['代码'] || old['交易对'];
          let neu = byCode[code];
          if (!neu) return;
          Object.keys(neu).forEach(k => {
            let ov = old[k], nv = neu[k];
            if (ov != nv) {
              old[k] = nv;
              changed = true;
              // 视觉闪动
              if (typeof nv === 'number' && (k.includes('涨跌') || k.includes('价') || k.includes('price') || k.includes('change'))) {
                let cell = document.querySelector('td[data-code="' + code + '"][data-field="' + k + '"]');
                if (cell) { cell.classList.remove('flash-up', 'flash-down'); void cell.offsetWidth; cell.classList.add(nv > ov ? 'flash-up' : 'flash-down'); }
              }
            }
          });
        });
        if (changed) {
          let now = Date.now(), timeStr = new Date().toLocaleTimeString();
          st.fetchTime = now;
          st.updateTime = timeStr;
          latestUpdate = now;
          _updateConnStatus(true);
          // 同步 4 处时间显示
          if (tab === m) {
            rows = st.rows;
            updateTime = st.updateTime;
            render();
          }
        }
        let ls = document.getElementById('liveStatus');
        if (ls) ls.innerHTML = '<span class="conn-dot on"></span>实时';
        let card = document.getElementById('card_' + m);
        if (card) card.querySelector('.card-count').textContent = st.rows.length + ' 条';
      } catch(e) {}
    };
    _sse.onerror = function() { _sse.close(); setTimeout(() => _connectSSE(m), 5000); };
  }

  // ─── 实时时钟 ───
  function refreshStamp() {
    document.getElementById('globalStamp').innerHTML = '实时时间：<span style="font-size:16px;font-weight:700" class="live">' + new Date().toLocaleTimeString() + '</span>';
    if (tab) {
      let s = ST[tab];
      if (s && s.fetchTime) {
        let ago = Math.round((Date.now() - s.fetchTime) / 1000);
        let ls = document.getElementById('liveStatus');
        if (ls) ls.innerHTML = ago < 15 ? '<span class="conn-dot on"></span>实时' : '<span class="conn-dot off"></span>' + ago + '秒前';
        // viewTime：客户端时间，每秒跳（独立于 SSE 推送）
        let vt = document.getElementById('viewTime');
        if (vt) vt.textContent = '更新 ' + new Date().toLocaleTimeString();
      }
    }
  }
  setInterval(refreshStamp, 1000);
  refreshStamp();

  // ─── 翻页/搜索 ───
  function goPage(a) {
    let tp = Math.ceil(rows.length / pageSize) || 1;
    if (a === 'first') page = 1; else if (a === 'prev') page = Math.max(1, page - 1);
    else if (a === 'next') page = Math.min(tp, page + 1); else if (a === 'last') page = tp;
    ST[tab] = { rows, cols, page, sortKey, sortDir, updateTime, search: document.getElementById('search').value };
    render();
  }
  function doFilter() { page = 1; render(); }

  function showToast(msg) {
    let t = document.getElementById('toast');
    t.textContent = msg; t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
  }

  // ─── 公开 API ───
  return {
    register, MODULES, registry, API,
    formatChinese, cacheGet, cacheSet,
    loadModule, openModule, startModule, startCrypto, closePanel,
    preloadAll, goPage, doFilter, sort: doSort, showToast,
    getTab: () => tab,
  };
})();

// 页面启动
document.addEventListener('DOMContentLoaded', () => MV.preloadAll());
