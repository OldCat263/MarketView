/**
 * 模块九：智能预测（V1.9.0）
 * 三 Tab: 信号列表 / 评分排行 / AI分析报告
 * 快速档: 纯本地评分 + 批量排名（<60s）
 * 完整档: 七维全开 + AI综合解读（~5s）
 */
MV.register({
  id: 'predict',
  name: '智能预测',
  icon: '🤖',
  endpoint: '/api/predict/rank/stock?limit=20',
  columns: ['代码', '名称', '总分', '缠论分', '量化分', '信号', '操作'],
  sortCol: '总分',
  renderMode: 'predict',
  tabIndent: true,
  lazy: true,

  // ─── 自定义渲染 ───
  renderFn: function(rows, cols) {
    var html = '';
    var module = document.getElementById('predictModule') ? document.getElementById('predictModule').value : 'stock';
    var period = document.getElementById('predictPeriod') ? document.getElementById('predictPeriod').value : '1d';

    // Tab 导航
    html += '<div class="predict-tabs" style="display:flex;gap:8px;padding:8px 0;border-bottom:1px solid var(--border)">';
    html += _tabBtn('tabSignals', '📊 信号列表', true);
    html += _tabBtn('tabRank', '🏆 评分排行', false);
    html += _tabBtn('tabAI', '🧠 AI分析报告', false);
    html += '</div>';

    // 工具栏
    html += '<div style="display:flex;gap:8px;align-items:center;padding:8px 0;flex-wrap:wrap">';
    html += '<select id="predictModule" onchange="MV.Predict.switchModule()" style="background:var(--card);color:var(--text);border:1px solid var(--border);padding:4px 8px;border-radius:4px">';
    ['stock','etf','hk','us','index','crypto'].forEach(function(m) {
      html += '<option value="' + m + '"' + (m === module ? ' selected' : '') + '>' + (MV.registry[m] ? MV.registry[m].name : m) + '</option>';
    });
    html += '</select>';
    html += '<select id="predictPeriod" onchange="MV.Predict.switchPeriod()" style="background:var(--card);color:var(--text);border:1px solid var(--border);padding:4px 8px;border-radius:4px">';
    html += '<option value="1d">日线</option><option value="1w">周线</option>';
    html += '</select>';
    html += '<button onclick="MV.Predict.loadRank()" style="background:var(--accent);color:#fff;border:none;padding:6px 16px;border-radius:4px;cursor:pointer">批量刷新</button>';
    html += '<span id="predictProgress" style="font-size:12px;color:var(--dim);margin-left:8px"></span>';
    html += '</div>';

    // Tab 内容区
    html += '<div id="tabSignals" class="predict-tab" style="display:block">';
    html += _buildSignalTable(predictState.signals);
    html += '</div>';

    html += '<div id="tabRank" class="predict-tab" style="display:none">';
    html += _buildRankTable(predictState.ranking);
    html += '</div>';

    html += '<div id="tabAI" class="predict-tab" style="display:none">';
    html += _buildAIReport(predictState.aiData);
    html += '</div>';

    document.getElementById('newsPanel').innerHTML = html;

    // 初始化 Tab 切换
    _initTabs();
  },

  format: function(v, col) {
    if (col === '总分' || col === '缠论分' || col === '量化分') return typeof v === 'number' ? v.toFixed(0) : String(v);
    if (col === '操作') return '';
    if (col === '名称') return v || '';
    return MV.formatChinese(v, col);
  },

  postProcess: function(r) { return r || []; },
  parseResponse: function(resp) { return (resp && resp.data) ? resp.data : []; }
});

// ─── 模块状态 ───
var predictState = {
  signals: [],
  ranking: [],
  aiData: null,
  currentModule: 'stock',
  currentPeriod: '1d',
  loading: false,
};

// ─── Tab 切换 ───
function _tabBtn(id, label, active) {
  return '<button class="predict-tab-btn' + (active ? ' active' : '') + '" id="btn_' + id + '" onclick="MV.Predict.switchTab(\'' + id + '\')" style="background:' + (active ? 'var(--accent)' : 'var(--card)') + ';color:' + (active ? '#fff' : 'var(--text)') + ';border:1px solid var(--border);padding:6px 14px;border-radius:4px;cursor:pointer;font-size:13px">' + label + '</button>';
}

function _initTabs() {
  var btns = document.querySelectorAll('.predict-tab-btn');
  btns.forEach(function(b) {
    b.addEventListener('click', function() {
      btns.forEach(function(x) { x.style.background = 'var(--card)'; x.style.color = 'var(--text)'; });
      b.style.background = 'var(--accent)'; b.style.color = '#fff';
    });
  });
}

// ─── 表格构建 ───
function _buildSignalTable(signals) {
  if (!signals || signals.length === 0) return '<div style="padding:32px;text-align:center;color:var(--dim)">暂无信号，点击"批量刷新"加载</div>';
  var html = '<div style="overflow-x:auto"><table style="width:100%;font-size:13px;border-collapse:collapse"><thead><tr><th style="padding:8px;text-align:left;border-bottom:1px solid var(--border)">代码</th><th style="padding:8px;text-align:left;border-bottom:1px solid var(--border)">名称</th><th style="padding:8px;text-align:left;border-bottom:1px solid var(--border)">信号</th><th style="padding:8px;text-align:right;border-bottom:1px solid var(--border)">价格</th><th style="padding:8px;text-align:right;border-bottom:1px solid var(--border)">置信度</th><th style="padding:8px;text-align:center;border-bottom:1px solid var(--border)">操作</th></tr></thead><tbody>';
  signals.slice(0, 30).forEach(function(s) {
    var score = s.score || {};
    var total = score.total_score || 50;
    html += '<tr><td style="padding:6px 8px;border-bottom:1px solid var(--border)">' + (s.code || '') + '</td><td style="padding:6px 8px;border-bottom:1px solid var(--border)">' + (s.name || '') + '</td><td style="padding:6px 8px;border-bottom:1px solid var(--border);color:' + (total >= 70 ? '#ef4444' : total >= 50 ? '#f59e0b' : '#22c55e') + '">' + (total >= 70 ? '买入' : total >= 50 ? '观望' : '卖出') + '</td><td style="padding:6px 8px;text-align:right;border-bottom:1px solid var(--border)">' + (total >= 50 ? '+' : '') + total.toFixed(0) + '</td><td style="padding:6px 8px;text-align:right;border-bottom:1px solid var(--border)">' + total.toFixed(0) + '%</td><td style="padding:6px 8px;text-align:center;border-bottom:1px solid var(--border)"><button onclick="MV.Predict.viewDetail(\'' + s.code + '\')" style="background:var(--accent);color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;font-size:12px">查看</button></td></tr>';
  });
  html += '</tbody></table></div>';
  return html;
}

function _buildRankTable(ranking) {
  if (!ranking || ranking.length === 0) return '<div style="padding:32px;text-align:center;color:var(--dim)">点击"批量刷新"加载排行数据</div>';
  var html = '<div style="overflow-x:auto"><table style="width:100%;font-size:13px;border-collapse:collapse"><thead><tr><th style="padding:8px;border-bottom:1px solid var(--border)">排名</th><th style="padding:8px;border-bottom:1px solid var(--border)">代码</th><th style="padding:8px;border-bottom:1px solid var(--border)">总分</th><th style="padding:8px;border-bottom:1px solid var(--border)">%</th><th style="padding:8px;border-bottom:1px solid var(--border)">缠论</th><th style="padding:8px;border-bottom:1px solid var(--border)">量化</th><th style="padding:8px;border-bottom:1px solid var(--border)">操作</th></tr></thead><tbody>';
  ranking.slice(0, 50).forEach(function(r, i) {
    var s = r.score || {};
    html += '<tr><td style="padding:4px 8px;border-bottom:1px solid var(--border);color:var(--dim)">' + (i + 1) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (r.code || '') + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border);font-weight:600">' + (s.total_score || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border);color:var(--dim)">前' + (r.pct_total || 50) + '%</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (s.chanlun || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)">' + (s.quant_factors || 0).toFixed(0) + '</td><td style="padding:4px 8px;border-bottom:1px solid var(--border)"><button onclick="MV.Predict.viewDetail(\'' + r.code + '\')" style="background:var(--accent);color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;font-size:12px">查看</button></td></tr>';
  });
  html += '</tbody></table></div>';
  return html;
}

function _buildAIReport(aiData) {
  if (!aiData || !aiData.ai) return '<div style="padding:32px;text-align:center;color:var(--dim)">点击信号列表的"查看"按钮触发AI分析</div>';
  var ai = aiData.ai;
  var score = aiData.score || {};
  var html = '<div style="padding:16px;max-height:60vh;overflow-y:auto;font-size:13px;line-height:1.8;color:var(--text)">';
  html += '<div style="margin-bottom:16px"><b style="color:var(--gold)">' + (aiData.name || aiData.code || '') + '</b> ' + (aiData.code || '') + '</div>';
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">';
  html += '<div style="padding:10px;background:var(--card);border-radius:4px"><div style="color:var(--dim);font-size:11px">综合评分</div><div style="font-size:24px;font-weight:bold;color:' + (score.total_score >= 70 ? '#ef4444' : '#f59e0b') + '">' + (score.total_score || 0).toFixed(0) + '</div></div>';
  html += '<div style="padding:10px;background:var(--card);border-radius:4px"><div style="color:var(--dim);font-size:11px">AI信号</div><div style="font-size:20px;font-weight:bold">' + (ai.signal === 'buy' ? '买入' : ai.signal === 'sell' ? '卖出' : '观望') + ' <span style="font-size:13px">置信度 ' + (ai.confidence || 50) + '</span></div></div>';
  html += '</div>';
  if (ai.analysis_text) {
    html += '<div style="white-space:pre-wrap;padding:12px;background:var(--card);border-radius:4px;max-height:300px;overflow-y:auto">' + ai.analysis_text + '</div>';
  }
  html += '<div style="margin-top:12px;padding:8px;color:var(--dim);font-size:11px;text-align:center;border-top:1px solid var(--border)">历史数据不代表未来收益，仅供参考 | AI: ' + (ai.source || 'unknown') + '</div>';
  html += '</div>';
  return html;
}

// ─── 对外 API ───
MV.Predict = {
  switchTab: function(tabId) {
    ['tabSignals','tabRank','tabAI'].forEach(function(id) {
      document.getElementById(id).style.display = (id === tabId) ? 'block' : 'none';
    });
  },

  switchModule: function() {
    predictState.currentModule = document.getElementById('predictModule').value;
    // 重新加载排行
    MV.Predict.loadRank();
  },

  switchPeriod: function() {
    predictState.currentPeriod = document.getElementById('predictPeriod').value;
  },

  loadRank: function() {
    var m = predictState.currentModule;
    var p = predictState.currentPeriod;
    var prog = document.getElementById('predictProgress');
    if (prog) prog.textContent = '加载中...';

    // 先触发批量计算
    fetch(MV.API + '/api/predict/batch/' + m + '?period=' + p + '&pool_size=200', { method: 'POST' })
      .then(function() {
        // 等 3s 后取结果
        setTimeout(function() {
          fetch(MV.API + '/api/predict/rank/' + m + '?period=' + p + '&limit=50')
            .then(function(r) { return r.json(); })
            .then(function(resp) {
              var data = resp.data || [];
              predictState.ranking = data;
              predictState.signals = data.slice(0, 30);
              if (prog) prog.textContent = data.length + ' 只已排行';
              // 重渲染
              MV.Predict.rerender();
            })
            .catch(function() { if (prog) prog.textContent = '加载失败'; });
        }, 3000);
      })
      .catch(function() { if (prog) prog.textContent = '触发失败'; });
  },

  viewDetail: function(code) {
    var m = predictState.currentModule;
    var p = predictState.currentPeriod;
    var prog = document.getElementById('predictProgress');
    if (prog) prog.textContent = '完整分析中...';

    fetch(MV.API + '/api/predict/analyze/' + m + '/' + code + '?period=' + p + '&count=200&with_ai=true')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        predictState.aiData = data;
        if (prog) prog.textContent = '分析完成 (' + (data.elapsed_ms || 0) + 'ms)';
        MV.Predict.switchTab('tabAI');
        MV.Predict.rerender();
      })
      .catch(function() { if (prog) prog.textContent = '分析失败'; });
  },

  rerender: function() {
    var cfg = MV.registry['predict'];
    if (cfg && cfg.renderFn) {
      cfg.renderFn(predictState.signals, []);
    }
  }
};
