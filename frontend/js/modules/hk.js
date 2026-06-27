// 模块四：港股 — 东财/新浪
MV.register({
  id: 'hk',
  icon: '🌏', name: '港股',
  endpoint: '/api/hk/spot',
  columns: ['代码','名称','最新价','涨跌幅','涨跌额','成交量','成交额','最高','最低','今开','昨收'],
  sortCol: '涨跌幅',
  format: MV.formatChinese,
  postProcess(rows) {
    return rows.map(r => {
      if (r['中文名称']) r['名称'] = r['中文名称'];
      if (r['英文名称'] && !r['名称']) r['名称'] = r['英文名称'];
      return r;
    });
  },
});
