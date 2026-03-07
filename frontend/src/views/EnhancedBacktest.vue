<template>
  <div class="enhanced-backtest">
    <div class="page-header">
      <h1>📈 增强回测系统</h1>
      <p>参考 Freqtrade、Backtrader、Jesse 的专业级回测</p>
    </div>

    <!-- 回测配置 -->
    <div class="card config-card">
      <h3>⚙️ 回测配置</h3>
      <div class="config-grid">
        <div class="config-item">
          <label>交易对</label>
          <select v-model="config.symbol" class="input-select">
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="BNBUSDT">BNB/USDT</option>
          </select>
        </div>
        <div class="config-item">
          <label>策略</label>
          <select v-model="config.strategy" class="input-select">
            <option value="ma_crossover">均线交叉策略</option>
            <option value="rsi">RSI 策略</option>
            <option value="bollinger">布林带策略</option>
          </select>
        </div>
        <div class="config-item">
          <label>初始资金</label>
          <input 
            v-model.number="config.initial_balance" 
            type="number" 
            class="input-number"
            min="100"
          >
        </div>
        <div class="config-item">
          <label>K线数量</label>
          <input 
            v-model.number="config.limit" 
            type="number" 
            class="input-number"
            min="100"
            max="2000"
          >
        </div>
      </div>
      <button 
        @click="runBacktest" 
        class="btn btn-primary btn-large"
        :disabled="isRunning"
      >
        {{ isRunning ? '⏳ 回测中...' : '🚀 开始回测' }}
      </button>
    </div>

    <!-- 策略说明 -->
    <div class="card">
      <h3>📚 可用策略</h3>
      <div class="strategies-list">
        <div 
          v-for="s in strategies" 
          :key="s.id"
          class="strategy-card"
          :class="{ active: config.strategy === s.id }"
          @click="config.strategy = s.id"
        >
          <div class="strategy-header">
            <h4>{{ s.name }}</h4>
          </div>
          <p class="strategy-desc">{{ s.description }}</p>
        </div>
      </div>
    </div>

    <!-- 回测结果 -->
    <div class="card results-card" v-if="backtestResult">
      <h3>📊 回测结果</h3>
      
      <!-- 主要指标 -->
      <div class="main-metrics">
        <div class="metric-card primary">
          <span class="metric-label">总收益率</span>
          <span class="metric-value primary" :class="profitClass">
            {{ backtestResult.metrics?.total_return_pct?.toFixed(2) }}%
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-label">年化收益率</span>
          <span class="metric-value">{{ backtestResult.metrics?.annual_return_pct?.toFixed(2) }}%</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">夏普比率</span>
          <span class="metric-value">{{ backtestResult.metrics?.sharpe_ratio?.toFixed(2) }}</span>
        </div>
        <div class="metric-card danger">
          <span class="metric-label">最大回撤</span>
          <span class="metric-value danger">{{ backtestResult.metrics?.max_drawdown_pct?.toFixed(2) }}%</span>
        </div>
      </div>

      <!-- 详细指标 -->
      <div class="detail-metrics">
        <h4>📋 详细指标</h4>
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-item-label">初始资金</span>
            <span class="metric-item-value">${{ backtestResult.initial_balance?.toLocaleString() }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">最终资金</span>
            <span class="metric-item-value">${{ backtestResult.final_balance?.toLocaleString() }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">总交易次数</span>
            <span class="metric-item-value">{{ backtestResult.total_trades }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">胜率</span>
            <span class="metric-item-value">{{ backtestResult.metrics?.win_rate_pct?.toFixed(1) }}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">卡玛比率</span>
            <span class="metric-item-value">{{ backtestResult.metrics?.calmar_ratio?.toFixed(2) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">盈亏比</span>
            <span class="metric-item-value">{{ backtestResult.metrics?.profit_factor?.toFixed(2) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">波动率</span>
            <span class="metric-item-value">{{ (backtestResult.metrics?.volatility * 100)?.toFixed(2) }}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">平均盈利</span>
            <span class="metric-item-value">${{ backtestResult.metrics?.avg_win?.toFixed(2) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-item-label">平均亏损</span>
            <span class="metric-item-value">${{ Math.abs(backtestResult.metrics?.avg_loss || 0)?.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- 交易记录 -->
      <div class="trades-section" v-if="backtestResult.trades?.length > 0">
        <h4>💹 交易记录</h4>
        <div class="trades-list">
          <div 
            v-for="(trade, idx) in backtestResult.trades.slice(0, 20)" 
            :key="idx"
            class="trade-item"
            :class="trade.side"
          >
            <span class="trade-side">{{ trade.side === 'buy' ? '🟢 买入' : '🔴 卖出' }}</span>
            <span class="trade-price">${{ trade.price?.toLocaleString() }}</span>
            <span class="trade-amount">{{ trade.amount?.toFixed(4) }}</span>
            <span class="trade-value">${{ trade.value?.toLocaleString() }}</span>
          </div>
        </div>
        <div v-if="backtestResult.trades.length > 20" class="more-trades">
          ... 还有 {{ backtestResult.trades.length - 20 }} 条记录
        </div>
      </div>
    </div>

    <!-- 快速测试 -->
    <div class="card quick-test-card">
      <h3>⚡ 快速测试</h3>
      <p class="quick-test-desc">使用随机策略进行快速回测演示</p>
      <button 
        @click="runQuickTest" 
        class="btn btn-secondary"
        :disabled="isRunning"
      >
        {{ isRunning ? '⏳ 测试中...' : '🧪 运行快速测试' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const config = ref({
  symbol: 'BTCUSDT',
  strategy: 'ma_crossover',
  initial_balance: 10000,
  interval: '1h',
  limit: 500
})

const isRunning = ref(false)
const backtestResult = ref<any>(null)
const strategies = ref<any[]>([])

const apiBase = '/api'

const profitClass = computed(() => {
  if (!backtestResult.value?.metrics) return ''
  return backtestResult.value.metrics.total_return >= 0 ? 'positive' : 'negative'
})

const fetchStrategies = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-backtest/strategies`)
    const data = await response.json()
    strategies.value = data.strategies || []
  } catch (error) {
    console.error('获取策略列表失败:', error)
  }
}

const runBacktest = async () => {
  isRunning.value = true
  backtestResult.value = null
  
  try {
    const response = await fetch(`${apiBase}/enhanced-backtest/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    })
    backtestResult.value = await response.json()
  } catch (error) {
    console.error('回测失败:', error)
  } finally {
    isRunning.value = false
  }
}

const runQuickTest = async () => {
  isRunning.value = true
  backtestResult.value = null
  
  try {
    const response = await fetch(
      `${apiBase}/enhanced-backtest/quick-test/${config.value.symbol}?strategy=${config.value.strategy}`
    )
    backtestResult.value = await response.json()
  } catch (error) {
    console.error('快速测试失败:', error)
  } finally {
    isRunning.value = false
  }
}

fetchStrategies()
</script>

<style scoped>
.enhanced-backtest {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #333;
}

.page-header p {
  margin: 0;
  color: #666;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.card h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.card h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.input-select,
.input-number {
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.input-select:focus,
.input-number:focus {
  border-color: #667eea;
}

.btn {
  padding: 12px 28px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-large {
  width: 100%;
  font-size: 16px;
  padding: 14px 32px;
}

.strategies-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.strategy-card {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.strategy-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #f8f9ff 0%, #e0e7ff 100%);
}

.strategy-header {
  margin-bottom: 8px;
}

.strategy-header h4 {
  margin: 0;
  font-size: 15px;
  color: #333;
}

.strategy-desc {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.main-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  text-align: center;
  padding: 20px;
  background: #f8f9ff;
  border-radius: 12px;
}

.metric-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-card.danger {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
}

.metric-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.metric-card.primary .metric-label,
.metric-card.danger .metric-label {
  color: rgba(255,255,255,0.9);
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.metric-card.primary .metric-value,
.metric-card.danger .metric-value {
  color: white;
}

.metric-value.primary.positive {
  color: #10b981;
}

.metric-value.primary.negative {
  color: #ef4444;
}

.detail-metrics {
  margin-bottom: 24px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8f9ff;
  border-radius: 8px;
}

.metric-item-label {
  color: #666;
  font-size: 13px;
}

.metric-item-value {
  font-weight: 600;
  color: #333;
}

.trades-section {
  margin-top: 24px;
}

.trades-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trade-item {
  display: grid;
  grid-template-columns: 100px 1fr 100px 1fr;
  gap: 12px;
  padding: 12px;
  background: #f8f9ff;
  border-radius: 8px;
  align-items: center;
}

.trade-item.buy {
  border-left: 3px solid #10b981;
}

.trade-item.sell {
  border-left: 3px solid #ef4444;
}

.trade-side {
  font-weight: 600;
}

.trade-price,
.trade-amount,
.trade-value {
  color: #666;
  font-size: 13px;
}

.more-trades {
  text-align: center;
  padding: 12px;
  color: #999;
  font-size: 13px;
}

.quick-test-card {
  text-align: center;
}

.quick-test-desc {
  color: #666;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .main-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .trade-item {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
}
</style>

