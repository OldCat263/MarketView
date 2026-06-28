/**
 * 模块九：智能预测（V2.2.8）
 * V2.2.8: SSE rank_update 加 module 字段，前端按当前模块过滤
 *        （修复 ETF 页面收到 stock 数据 + 切换模块时数据串台）
 * 评分排行常驻显示 → 点「查看」在下方展开分析报告
 * 分页：每页 20 条，按总分降序排列
 */
MV.register({
  id: 'predict',
  name: '智能预测',
  icon: '🤖',
  endpoint: '/api/predict/rank/stock?limit=200',
  columns: ['代码', '名称', '总分', '缠论分', '量化分', '信号', '操作'],
  sortCol: '总分',
  renderMode: 'predict',
  tabIndent: true,
  lazy: true,

  renderFn: function(rows, cols) {
    var html = '';
    var module = predictState.currentModule;
    var period = predictState.currentPeriod;

    // 工具栏
    html += '<div style="display:flex;gap:8px;align-items:center;padding:8px 0;flex-wrap:wrap">';
    html += '<select id="predictModule" onchange="MV.Predict.switchModule()" style="background:var(--card);color:var(--text);border:1px solid var(--border);padding:4px 8px;border-radius:4px">';
    // V2.2.5: 只支持 stock + etf（V2.2.0 起预测只做这两个模块）
    ['stock','etf'].forEach(function(m) {
      html += '<option value="' + m + '"' + (m === module ? ' selected' : '') + '>' + (MV.registry[m] ? MV.registry[m].name : m) + '</option>';
    });
    html += '</select>';
    html += '<select id="predictPeriod" onchange="MV.Predict.switchPeriod()" style="background:var(--card);color:var(--text);border:1px solid var(--border);padding:4px 8px;border-radius:4px">';
    html += '<option value="1d"'+ (period==='1d'?' selected':'') +'>日线</option><option value="1w"'+ (period==='1w'?' selected':'') +'>周线</option>';
    html += '</select>';
    html += '<button onclick="MV.Predict.loadRank()" style="background:var(--accent);color:#fff;border:none;padding:6px 16px;border-radius:4px;cursor:pointer">批量刷新</button>';
    html += '<span id="predictProgress" style="font-size:12px;color:var(--dim);margin-left:8px"></span>';
    html += '</div>';

    // 风险提示
    html += '<div style="margin:8px 0;padding:8px 12px;background:var(--card);border-left:3px solid #f59e0b;border-radius:4px;font-size:12px;color:var(--dim);line-height:1.6">' +
      '⚠️ <b>免责声明</b>：本预测指标仅适用于 <b>A股、ETF、指数</b>。评分结果仅供参考，不构成任何投资建议。</div>';

    // ── 评分排行表格（始终显示）──
    html += '<div id="rankArea">';
    html += _buildRankTable(predictState.ranking, predictState.rankPage || 1, 20);
    html += '</div>';

    // ── AI 分析报告区（下方原位展开）──
    html += '<div id="aiArea" style="margin-top:12px;' + (predictState.aiData ? '' : 'display:none') + '">';
    if (predictState.aiData) {
      html += _buildAIReport(predictState.aiData);
    }
    html += '</div>';

    document.getElementById('predictPanel').innerHTML = html;
  },

  format: function(v, col) {
    if (col === '总分' || col === '缠论分' || col === '量化分') return typeof v === 'number' ? v.toFixed(0) : String(v);
    if (col === '操作') return '';
    if (col === '名称') return v || '';
    return MV.formatChinese(v, col);
  },

  postProcess: function(r) { return r || []; },
  parseResponse: function(resp) {
    var data = (resp && resp.data) ? resp.data : [];
    data.sort(function(a, b) {
      var sa = a.score ? a.score.total_score || 0 : 0;
      var sb = b.score ? b.score.total_score || 0 : 0;
      return sb - sa;
    });
    predictState.ranking = data;
    predictState.signals = data.slice(0, 30);
    return data;
  }
});

// ─── 模块状态 ───
var predictState = {
  signals: [],
  ranking: [],
  aiData: null,
  currentModule: 'stock',
  currentPeriod: '1d',
  rankPage: 1,
  loading: false
};

// ─── 评分排行（分页）───
function _buildRankTable(ranking, page, pageSize) {
  page = page || 1;
  pageSize = pageSize || 20;
  if (!ranking || ranking.length === 0) return '<div style="padding:32px;text-align:center;color:var(--dim)">点击"批量刷新"加载排行数据</div>';

  var sorted = ranking.slice().sort(function(a, b) {
    var sa = a.score ? a.score.total_score || 0 : 0;
    var sb = b.score ? b.score.total_score || 0 : 0;
    return sb - sa;
  });

  var total = sorted.length;
  var totalPages = Math.ceil(total / pageSize) || 1;
  if (page > totalPages) page = totalPages;
  var start = (page - 1) * pageSize;
  var pageData = sorted.slice(start, start + pageSize);

  var html = '';

  // 分页栏（上方）
  html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;margin-bottom:4px">';
  html += '<span style="font-size:12px;color:var(--dim)">共 ' + total + ' 条，第 ' + page + '/' + totalPages + ' 页</span>';
  html += '<div style="display:flex;gap:4px">';
  html += '<button onclick="MV.Predict.goRankPage(' + (page - 1) + ')" ' + (page <= 1 ? 'disabled' : '') + ' style="background:var(--card);color:' + (page <= 1 ? 'var(--dim)' : 'var(--text)') + ';border:1px solid var(--border);padding:3px 10px;border-radius:3px;cursor:' + (page <= 1 ? 'default' : 'pointer') + ';font-size:12px">◀ 上一页</button>';
  html += '<button onclick="MV.Predict.goRankPage(' + (page + 1) + ')" ' + (page >= totalPages ? 'disabled' : '') + ' style="background:var(--card);color:' + (page >= totalPages ? 'var(--dim)' : 'var(--text)') + ';border:1px solid var(--border);padding:3px 10px;border-radius:3px;cursor:' + (page >= totalPages ? 'default' : 'pointer') + ';font-size:12px">下一页 ▶</button>';
  html += '</div></div>';

  // 表格
  html += '<div style="overflow-x:auto"><table style="width:100%;font-size:13px;border-collapse:collapse"><thead><tr><th style="padding:8px;border-bottom:1px solid var(--border)">排名</th><th style="padding:8px;border-bottom:1px solid var(--border)">代码</th><th style="padding:8px;border-bottom:1px solid var(--border)">名称</th><th style="padding:8px;border-bottom:1px solid var(--border)">总分</th><th style="padding:8px;border-bottom:1px solid var(--border)">%</th><th style="padding:8px;border-bottom:1px solid var(--border)">缠论</th><th style="padding:8px;border-bottom:1px solid var(--border)">量化</th><th style="padding:8px;border-bottom:1px solid var(--border)">操作</th></tr></thead><tbody>';
  pageData.forEach(function(r, i) {
    var s = r.score || {};
    var idx = start + i + 1;
    html += '<tr><td style="padding:4px 8px;border-bottom:1px solid var(--border);color:var(--dim)">' + idx + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (r.code || '') + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (r.name || '') + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border);font-weight:600">' + (s.total_score || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border);color:var(--dim)">前' + (r.pct_total || 50) + '%</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (s.chanlun || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (s.quant_factors || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)"><button onclick="MV.Predict.viewDetail(\'' + r.code + '\')" style="background:var(--accent);color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;font-size:12px">查看</button></td></tr>';
  });
  html += '</tbody></table></div>';

  // 分页栏（下方）
  html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;margin-top:4px">';
  html += '<span style="font-size:12px;color:var(--dim)">共 ' + total + ' 条，第 ' + page + '/' + totalPages + ' 页</span>';
  html += '<div style="display:flex;gap:4px">';
  html += '<button onclick="MV.Predict.goRankPage(' + (page - 1) + ')" ' + (page <= 1 ? 'disabled' : '') + ' style="background:var(--card);color:' + (page <= 1 ? 'var(--dim)' : 'var(--text)') + ';border:1px solid var(--border);padding:3px 10px;border-radius:3px;cursor:' + (page <= 1 ? 'default' : 'pointer') + ';font-size:12px">◀ 上一页</button>';
  html += '<button onclick="MV.Predict.goRankPage(' + (page + 1) + ')" ' + (page >= totalPages ? 'disabled' : '') + ' style="background:var(--card);color:' + (page >= totalPages ? 'var(--dim)' : 'var(--text)') + ';border:1px solid var(--border);padding:3px 10px;border-radius:3px;cursor:' + (page >= totalPages ? 'default' : 'pointer') + ';font-size:12px">下一页 ▶</button>';
  html += '</div></div>';

  return html;
}

// ─── AI 报告（在表格下方展开）───
function _buildAIReport(aiData) {
  if (!aiData) return '';
  var ai = aiData.ai;
  var score = aiData.score || {};
  var html = '';

  // 关闭按钮条
  html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--card);border-radius:4px 4px 0 0;border:1px solid var(--border);border-bottom:none">';
  html += '<b style="color:var(--gold)">🧠 ' + (aiData.name || aiData.code || '') + ' ' + (aiData.code || '') + ' · 综合评分 ' + (score.total_score || 0).toFixed(0) + '</b>';
  html += '<button onclick="MV.Predict.closeAI()" style="background:transparent;color:var(--dim);border:1px solid var(--border);padding:4px 10px;border-radius:3px;cursor:pointer;font-size:12px">✕ 收起报告</button>';
  html += '</div>';

  html += '<div style="padding:12px;max-height:60vh;overflow-y:auto;font-size:13px;line-height:1.8;color:var(--text);background:var(--card);border:1px solid var(--border);border-top:none;border-radius:0 0 4px 4px">';

  // 评分卡片
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">';
  html += '<div style="padding:10px;background:var(--bg);border-radius:4px"><div style="color:var(--dim);font-size:11px">综合评分</div><div style="font-size:24px;font-weight:bold;color:' + (score.total_score >= 70 ? '#ef4444' : '#f59e0b') + '">' + (score.total_score || 0).toFixed(0) + '</div></div>';
  html += '<div style="padding:10px;background:var(--bg);border-radius:4px"><div style="color:var(--dim);font-size:11px">AI信号</div><div style="font-size:20px;font-weight:bold">' + (ai.signal === 'buy' ? '🟢 买入' : ai.signal === 'sell' ? '🔴 卖出' : '🟡 观望') + ' <span style="font-size:13px;color:var(--dim)">置信度 ' + (ai.confidence || 50) + '</span></div></div>';
  html += '</div>';

  if (ai.analysis_text) {
    html += '<div style="white-space:pre-wrap;padding:10px;background:var(--bg);border-radius:4px;max-height:260px;overflow-y:auto">' + ai.analysis_text + '</div>';
  }

  html += '<div style="margin-top:12px;padding:8px;color:var(--dim);font-size:11px;text-align:center;border-top:1px solid var(--border)">⚠️ 历史数据不代表未来收益，仅供参考 | AI: ' + (ai.source || 'unknown') + '</div>';
  html += '</div>';

  return html;
}

// ─── 对外 API ───
MV.Predict = {
  goRankPage: function(page) {
    if (!predictState.ranking || !predictState.ranking.length) return;
    var totalPages = Math.ceil(predictState.ranking.length / 20) || 1;
    if (page < 1 || page > totalPages) return;
    predictState.rankPage = page;
    var el = document.getElementById('rankArea');
    if (el) el.innerHTML = _buildRankTable(predictState.ranking, page, 20);
  },

  switchModule: function() {
    predictState.currentModule = document.getElementById('predictModule').value;
    predictState.rankPage = 1;
    MV.Predict.loadRank();
  },

  switchPeriod: function() {
    predictState.currentPeriod = document.getElementById('predictPeriod').value;
    predictState.rankPage = 1;
    MV.Predict.loadRank();
  },

  loadRank: function() {
    var m = predictState.currentModule;
    var p = predictState.currentPeriod;
    var prog = document.getElementById('predictProgress');
    if (prog) prog.textContent = '连接中...';

    if (this._sse) { this._sse.close(); this._sse = null; }

    fetch(MV.API + '/api/predict/batch/' + m + '?period=' + p + '&pool_size=200', { method: 'POST' });
    predictState.rankPage = 1;

    var self = this;
    this._sse = new EventSource(MV.API + '/api/stream/predict/' + m);
    this._sse._reconnCount = 0;
    this._sse.onmessage = function(e) {
      try {
        var msg = JSON.parse(e.data);
        if (msg.type === 'rank_update') {
          // V2.2.8: 按 module 过滤（之前会因为共享队列导致 ETF 页面收到 stock 数据）
          if (msg.module && msg.module !== predictState.currentModule) return;
          var data = msg.data || [];
          data.sort(function(a, b) {
            var sa = a.score ? a.score.total_score || 0 : 0;
            var sb = b.score ? b.score.total_score || 0 : 0;
            return sb - sa;
          });
          predictState.ranking = data;
          predictState.signals = data.slice(0, 30);
          if (prog) prog.textContent = data.length + ' 只已排行';
          self.rerender();
          self._sse.close();
          self._sse = null;
        }
      } catch(ex) {}
    };
    this._sse.onerror = function() {
      this._reconnCount = (this._reconnCount || 0) + 1;
      if (this._reconnCount >= 3) {
        this.close();
        self._sse = null;
        if (prog) prog.textContent = '连接失败，请重试';
      } else {
        if (prog) prog.textContent = '重连中 (' + this._reconnCount + '/3)';
      }
    };
  },

  viewDetail: function(code) {
    var m = predictState.currentModule;
    var p = predictState.currentPeriod;
    var prog = document.getElementById('predictProgress');
    if (prog) prog.textContent = '完整分析中...';

    fetch(MV.API + '/api/predict/analyze/' + m + '/' + code + '?period=' + p + '&count=100&with_ai=true')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        predictState.aiData = data;
        if (prog) prog.textContent = '分析完成 (' + (data.elapsed_ms || 0) + 'ms)';
        // 在表格下方原位展开，不切 Tab
        var aiArea = document.getElementById('aiArea');
        if (aiArea) {
          aiArea.innerHTML = _buildAIReport(data);
          aiArea.style.display = '';
          aiArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        // 高亮当前行
        var rows = document.querySelectorAll('#rankArea tr');
        rows.forEach(function(r) { r.style.background = ''; });
        rows.forEach(function(r) {
          if (r.textContent.indexOf(code) !== -1) r.style.background = 'var(--accent-bg)';
        });
      })
      .catch(function() {
        if (prog) prog.textContent = '分析失败';
      });
  },

  closeAI: function() {
    predictState.aiData = null;
    var aiArea = document.getElementById('aiArea');
    if (aiArea) { aiArea.style.display = 'none'; aiArea.innerHTML = ''; }
    var rows = document.querySelectorAll('#rankArea tr');
    rows.forEach(function(r) { r.style.background = ''; });
  },

  rerender: function() {
    var cfg = MV.registry['predict'];
    if (cfg && cfg.renderFn) {
      cfg.renderFn(predictState.signals, []);
    }
  }
};
