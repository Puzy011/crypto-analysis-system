import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('Response error:', error)
    
    // 统一错误处理
    if (error.response) {
      switch (error.response.status) {
        case 400:
          console.error('请求参数错误')
          break
        case 401:
          console.error('未授权，请登录')
          break
        case 403:
          console.error('拒绝访问')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
        default:
          console.error('请求失败')
      }
    } else if (error.request) {
      console.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default api

// API 接口定义
export const marketApi = {
  // 获取市场行情
  getMarketData: (symbols?: string[]) => 
    api.get('/api/market/data', { params: { symbols: symbols?.join(',') } }),
  
  // 获取K线数据
  getKlineData: (symbol: string, interval: string, limit?: number) =>
    api.get('/api/market/kline', { params: { symbol, interval, limit } })
}

export const predictionApi = {
  // 基础预测
  predict: (symbol: string, interval: string) =>
    api.post('/api/prediction/predict', { symbol, interval }),
  
  // 高级预测
  advancedPredict: (symbol: string, interval: string, models?: string[]) =>
    api.post('/api/advanced-prediction/predict', { symbol, interval, models }),
  
  // 实时预测
  realtimePredict: (symbol: string) =>
    api.get('/api/realtime-prediction/predict', { params: { symbol } })
}

export const whaleApi = {
  // 庄家分析
  analyze: (symbol: string, interval: string) =>
    api.post('/api/whale/analyze', { symbol, interval }),
  
  // 巨鲸分析
  whaleAnalysis: (symbol: string, timeframe: string) =>
    api.post('/api/whale-analysis/analyze', { symbol, timeframe })
}

export const sentimentApi = {
  // 基础舆情
  analyze: (symbol: string) =>
    api.post('/api/sentiment/analyze', { symbol }),
  
  // 增强舆情
  enhancedAnalyze: (symbol: string, sources?: string[]) =>
    api.post('/api/enhanced-sentiment/analyze', { symbol, sources }),
  
  // 实时舆情
  realtimeAnalyze: (symbol: string) =>
    api.get('/api/realtime-sentiment/analyze', { params: { symbol } }),
  
  // 综合舆情
  comprehensiveAnalyze: (symbol: string) =>
    api.post('/api/comprehensive-sentiment/analyze', { symbol })
}

export const technicalApi = {
  // 完整技术指标
  analyze: (symbol: string, interval: string) =>
    api.post('/api/complete-ta/analyze', { symbol, interval })
}

export const backtestApi = {
  // 预测回测
  backtest: (symbol: string, interval: string, days: number) =>
    api.post('/api/prediction-backtest/backtest', { symbol, interval, days }),
  
  // 增强回测
  enhancedBacktest: (symbol: string, strategy: any, params: any) =>
    api.post('/api/enhanced-backtest/backtest', { symbol, strategy, params })
}

export const healthApi = {
  // 健康检查
  check: () => api.get('/api/health')
}
