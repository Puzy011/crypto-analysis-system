/**
 * 常量配置
 */

// 交易对列表
export const SYMBOLS = [
  { value: 'BTCUSDT', label: 'BTC/USDT', name: 'Bitcoin' },
  { value: 'ETHUSDT', label: 'ETH/USDT', name: 'Ethereum' },
  { value: 'BNBUSDT', label: 'BNB/USDT', name: 'Binance Coin' },
  { value: 'SOLUSDT', label: 'SOL/USDT', name: 'Solana' },
  { value: 'XRPUSDT', label: 'XRP/USDT', name: 'Ripple' },
  { value: 'ADAUSDT', label: 'ADA/USDT', name: 'Cardano' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT', name: 'Dogecoin' },
  { value: 'DOTUSDT', label: 'DOT/USDT', name: 'Polkadot' },
  { value: 'MATICUSDT', label: 'MATIC/USDT', name: 'Polygon' },
  { value: 'AVAXUSDT', label: 'AVAX/USDT', name: 'Avalanche' }
]

// K线时间间隔
export const INTERVALS = [
  { value: '1m', label: '1分钟' },
  { value: '3m', label: '3分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '30m', label: '30分钟' },
  { value: '1h', label: '1小时' },
  { value: '2h', label: '2小时' },
  { value: '4h', label: '4小时' },
  { value: '6h', label: '6小时' },
  { value: '12h', label: '12小时' },
  { value: '1d', label: '1天' },
  { value: '3d', label: '3天' },
  { value: '1w', label: '1周' },
  { value: '1M', label: '1月' }
]

// 预测模型
export const PREDICTION_MODELS = [
  { value: 'xgboost', label: 'XGBoost', description: '梯度提升决策树' },
  { value: 'lightgbm', label: 'LightGBM', description: '轻量级梯度提升' },
  { value: 'prophet', label: 'Prophet', description: '时间序列预测' },
  { value: 'random_forest', label: 'Random Forest', description: '随机森林' },
  { value: 'ensemble', label: 'Ensemble', description: '集成学习' }
]

// 技术指标
export const TECHNICAL_INDICATORS = [
  { value: 'ma', label: 'MA', name: '移动平均线' },
  { value: 'ema', label: 'EMA', name: '指数移动平均' },
  { value: 'macd', label: 'MACD', name: 'MACD指标' },
  { value: 'rsi', label: 'RSI', name: '相对强弱指标' },
  { value: 'bollinger', label: 'BOLL', name: '布林带' },
  { value: 'kdj', label: 'KDJ', name: 'KDJ指标' },
  { value: 'obv', label: 'OBV', name: '能量潮' },
  { value: 'atr', label: 'ATR', name: '真实波幅' }
]

// 舆情来源
export const SENTIMENT_SOURCES = [
  { value: 'twitter', label: 'Twitter', icon: '🐦' },
  { value: 'reddit', label: 'Reddit', icon: '🤖' },
  { value: 'news', label: 'News', icon: '📰' },
  { value: 'telegram', label: 'Telegram', icon: '✈️' },
  { value: 'discord', label: 'Discord', icon: '💬' }
]

// 情感类型
export const SENTIMENT_TYPES = [
  { value: 'positive', label: '积极', color: '#67C23A' },
  { value: 'neutral', label: '中性', color: '#909399' },
  { value: 'negative', label: '消极', color: '#F56C6C' }
]

// 庄家操作阶段
export const WHALE_PHASES = [
  { value: 'accumulation', label: '吸筹', color: '#409EFF', description: '庄家建仓阶段' },
  { value: 'wash', label: '洗盘', color: '#E6A23C', description: '震荡清洗浮筹' },
  { value: 'pump', label: '拉升', color: '#67C23A', description: '快速拉升价格' },
  { value: 'distribution', label: '出货', color: '#F56C6C', description: '高位派发筹码' }
]

// 回测时间范围
export const BACKTEST_PERIODS = [
  { value: 7, label: '7天' },
  { value: 14, label: '14天' },
  { value: 30, label: '30天' },
  { value: 60, label: '60天' },
  { value: 90, label: '90天' }
]

// 图表主题颜色
export const CHART_COLORS = {
  up: '#26a69a',      // 上涨颜色（绿色）
  down: '#ef5350',    // 下跌颜色（红色）
  line: '#2962FF',    // 线条颜色
  grid: '#e0e0e0',    // 网格颜色
  text: '#333333',    // 文字颜色
  background: '#ffffff' // 背景颜色
}

// 刷新间隔（毫秒）
export const REFRESH_INTERVALS = {
  realtime: 5000,     // 实时数据：5秒
  market: 10000,      // 市场数据：10秒
  prediction: 30000,  // 预测数据：30秒
  sentiment: 60000    // 舆情数据：60秒
}

// 分页配置
export const PAGINATION = {
  pageSize: 20,
  pageSizes: [10, 20, 50, 100]
}

// API 状态码
export const API_STATUS = {
  SUCCESS: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500
}
