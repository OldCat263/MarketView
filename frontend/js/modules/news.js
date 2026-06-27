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
      var link = r.url || '';
      // 显示日期+时间（YYYY-MM-DD HH:MM:SS，同日省略年份）
      var dateDisplay = '';
      var timeDisplay = '';
      if (dt.length > 10) {
        var yearPart = dt.substring(0, 4);     // YYYY
        var datePart = dt.substring(0, 10);     // YYYY-MM-DD
        var timePart = dt.substring(11);         // HH:MM:SS
        var today = new Date();
        var todayStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0');
        dateDisplay = (datePart === todayStr) ? '' : yearPart + '-' + datePart.substring(5) + ' ';  // 非今日显示 YYYY-MM-DD
        timeDisplay = timePart;
      } else {
        timeDisplay = dt;
      }
      // 有链接时卡片可点击跳转
      var cardTag = link ? 'a' : 'div';
      var cardAttrs = link ? ' href="' + link + '" target="_blank" rel="noopener"' : '';
      html += '<' + cardTag + ' class="news-card"' + cardAttrs + '>'
        + '<div class="news-card-header">'
        + '<span class="news-time">' + dateDisplay + timeDisplay + '</span>'
        + '<span class="news-source">' + src + '</span>'
        + '</div>'
        + '<div class="news-content">' + ct + '</div>'
        + '</' + cardTag + '>';
    }
  }
  panel.innerHTML = html;
  // 更新计数
  document.getElementById('count').textContent = filtered.length + ' 条';
}
