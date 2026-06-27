// 模块八：新闻 — 卡片流渲染（V1.8.0）
// 数据源：新浪财经（主）→ 财新头条（备）
// 渲染：时间倒序卡片流，搜索过滤，无翻页
MV.register({
  id: 'news',
  icon: '📰', name: '新闻',
  endpoint: '/api/news/spot',
  columns: ['datetime', 'content', 'source', 'url'],
  sortCol: 'datetime',
  renderMode: 'news',
  renderFn: renderNews,
  placeholder: false,
});

function renderNews(rows, cols) {
  var panel = document.getElementById('newsPanel');
  if (!panel) return;
  var q = (document.getElementById('search').value || '').trim().toLowerCase();
  var filtered = q ? rows.filter(function(r) { return (r.content || '').toLowerCase().includes(q) || (r.source || '').toLowerCase().includes(q); }) : rows;

  var html = '';
  if (!filtered.length) {
    html = '<div class="news-empty">暂无新闻</div>';
  } else {
    for (var i = 0; i < filtered.length; i++) {
      var r = filtered[i];
      var dt = r.datetime || '';
      var ct = r.content || '';
      var src = r.source || '';
      var url = r.url || '';
      // 日期+时间（如含日期则显示 MM-DD HH:MM，否则原样）
      var timeDisplay = dt;
      if (dt.length >= 16) {
        timeDisplay = dt.substring(0, 16);  // "YYYY-MM-DD HH:MM"
      }
      var clickAttr = url ? ' onclick="window.open(\'' + url.replace(/'/g, "\\'") + '\')" style="cursor:pointer"' : '';
      html += '<div class="news-card"' + clickAttr + '>'
        + '<div class="news-card-header">'
        + '<span class="news-time">' + timeDisplay + '</span>'
        + '<span class="news-source">' + src + '</span>'
        + '</div>'
        + '<div class="news-content">' + ct + '</div>'
        + '</div>';
    }
  }
  panel.innerHTML = html;
  // 更新计数
  document.getElementById('count').textContent = filtered.length + ' 条';
}
