// 模块二：A股 — 腾讯 qt.gtimg.cn 优先
MV.register({
  id: 'stock',
  icon: '📈', name: 'A股',
  endpoint: '/api/stock/spot',
  columns: ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额','振幅','最高','最低','今开','昨收','换手率','量比'],
  sortCol: '涨跌幅',
  format: MV.formatChinese,
});
