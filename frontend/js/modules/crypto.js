// 模块一：加密货币 — Binance API
MV.register({
  id: 'crypto',
  icon: '🪙', name: '加密货币',
  endpoint: '/api/crypto/spot',
  columns: ['交易对','价格(USD)','24h涨跌','24h最高','24h最低','成交量','成交额(USD)'],
  sortCol: '24h涨跌',
  format(cellValue, colName) {
    if (typeof cellValue !== 'number') return String(cellValue);
    if (colName.includes('价格')) return '$' + cellValue.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
    if (colName.includes('涨跌')) return (cellValue > 0 ? '+' : '') + cellValue + '%';
    if (colName.includes('成交额')) return '$' + (cellValue / 1e9).toFixed(2) + 'B';
    if (colName.includes('成交量')) return (cellValue / 1e6).toFixed(2) + 'M';
    return cellValue.toFixed(2);
  },
  postProcess(rows) { return rows; },
  tabIndent: true,  // 加密每格加缩进
  lazy: true,       // 需要代理检测
});
