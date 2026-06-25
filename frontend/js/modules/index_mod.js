// 模块六：指数 — 东财/新浪
MV.register({
  id: 'index',
  icon: '📉', name: '指数',
  endpoint: '/api/index/spot',
  columns: ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额'],
  sortCol: '涨跌幅',
  format: MV.formatChinese,
  parseResponse(resp) {
    return [...(resp.data.china || []), ...(resp.data.global || [])];
  },
  postProcess(rows) {
    return rows.map(r => { if (!r['名称'] || r['名称'] === '') r['名称'] = '数据源错误'; return r; });
  },
});
