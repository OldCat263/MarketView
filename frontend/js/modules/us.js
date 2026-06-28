// 模块五：美股 — 腾讯 qt.gtimg.cn（V2.1.0 秒级）
MV.register({
  id: 'us',
  icon: '🇺🇸', name: '美股',
  endpoint: '/api/us/spot',
  columns: ['代码','名称','分类','最新价','涨跌幅','涨跌额','成交量','成交额','最高','最低','今开','昨收'],
  sortCol: '涨跌幅',
  format: MV.formatChinese,
  // V2.1.0: 分类筛选器
  categoryFilter: ['全部','中概股','全球龙头','中概ETF','港股ADR'],
  postProcess(rows) {
    return rows.map(r => {
      if (r['中文名称']) r['名称'] = r['中文名称'];
      if (r['英文名称'] && !r['名称']) r['名称'] = r['英文名称'];
      return r;
    });
  },
});
