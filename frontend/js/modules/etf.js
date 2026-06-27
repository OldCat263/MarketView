// 模块三：ETF — 东财 fund_etf_spot_em
MV.register({
  id: 'etf',
  icon: '📊', name: 'ETF',
  endpoint: '/api/etf/spot',
  columns: ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额','振幅','最高价','最低价','今开','昨收','换手率'],
  sortCol: '涨跌幅',
  format: MV.formatChinese,
});
