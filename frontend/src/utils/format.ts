/**
 * 格式化工具函数
 */

/**
 * 格式化数字为货币格式
 * @param value 数值
 * @param decimals 小数位数
 * @param symbol 货币符号
 */
export function formatCurrency(value: number, decimals: number = 2, symbol: string = '$'): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-'
  }
  return `${symbol}${value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
}

/**
 * 格式化百分比
 * @param value 数值
 * @param decimals 小数位数
 */
export function formatPercent(value: number, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-'
  }
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

/**
 * 格式化大数字（K, M, B）
 * @param value 数值
 * @param decimals 小数位数
 */
export function formatLargeNumber(value: number, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-'
  }
  
  const absValue = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  
  if (absValue >= 1e9) {
    return `${sign}${(absValue / 1e9).toFixed(decimals)}B`
  } else if (absValue >= 1e6) {
    return `${sign}${(absValue / 1e6).toFixed(decimals)}M`
  } else if (absValue >= 1e3) {
    return `${sign}${(absValue / 1e3).toFixed(decimals)}K`
  }
  
  return `${sign}${absValue.toFixed(decimals)}`
}

/**
 * 格式化时间戳
 * @param timestamp 时间戳（毫秒）
 * @param format 格式
 */
export function formatTimestamp(timestamp: number, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!timestamp) {
    return '-'
  }
  
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化交易对符号
 * @param symbol 交易对符号（如 BTCUSDT）
 */
export function formatSymbol(symbol: string): string {
  if (!symbol) {
    return '-'
  }
  
  // 常见的基础货币
  const baseCurrencies = ['USDT', 'USDC', 'BUSD', 'USD', 'BTC', 'ETH', 'BNB']
  
  for (const base of baseCurrencies) {
    if (symbol.endsWith(base)) {
      const quote = symbol.slice(0, -base.length)
      return `${quote}/${base}`
    }
  }
  
  return symbol
}

/**
 * 获取涨跌颜色类型
 * @param value 数值
 */
export function getChangeColorType(value: number): 'success' | 'danger' | 'info' {
  if (value > 0) return 'success'
  if (value < 0) return 'danger'
  return 'info'
}

/**
 * 格式化时间间隔
 * @param interval 时间间隔（如 1m, 5m, 1h, 1d）
 */
export function formatInterval(interval: string): string {
  const intervalMap: Record<string, string> = {
    '1m': '1分钟',
    '3m': '3分钟',
    '5m': '5分钟',
    '15m': '15分钟',
    '30m': '30分钟',
    '1h': '1小时',
    '2h': '2小时',
    '4h': '4小时',
    '6h': '6小时',
    '8h': '8小时',
    '12h': '12小时',
    '1d': '1天',
    '3d': '3天',
    '1w': '1周',
    '1M': '1月'
  }
  
  return intervalMap[interval] || interval
}

/**
 * 截断文本
 * @param text 文本
 * @param maxLength 最大长度
 * @param suffix 后缀
 */
export function truncateText(text: string, maxLength: number = 50, suffix: string = '...'): string {
  if (!text || text.length <= maxLength) {
    return text
  }
  
  return text.slice(0, maxLength) + suffix
}
