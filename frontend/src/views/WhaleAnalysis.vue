<template>
  <div class="whale-analysis">
    <div class="page-header">
      <h1>🐋 巨鲸/庄家分析</h1>
      <p>OrderFlow 风格订单流分析 + 大单检测 + 庄家阶段识别</p>
    </div>

    <!-- 综合分析 -->
    <div class="card overall-card" :class="whaleAnalysis?.overall?.risk_level">
      <div class="overall-main">
        <div class="overall-emoji">{{ whaleAnalysis?.overall?.risk_emoji }}</div>
        <div class="overall-info">
          <h3>{{ whaleAnalysis?.overall?.risk_message }}</h3>
          <div class="overall-signals">
            <span class="signal bullish">
              🟢 多头信号: {{ whaleAnalysis?.overall?.bullish_signals || 0 }}
            </span>
            <span class="signal bearish">
              🔴 空头信号: {{ whaleAnalysis?.overall?.bearish_signals || 0 }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 大单检测 -->
    <div class="card">
      <h3>💎 大单检测</h3>
      <div class="large-orders" v-if="largeOrders">
        <div class="orders-summary">
          <div class="summary-item">
            <span class="summary-label">大单总数</span>
            <span class="summary-value">{{ largeOrders.total_large_orders }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">买单</span>
            <span class="summary-value buy">{{ largeOrders.buy_orders }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">卖单</span>
            <span class="summary-value sell">{{ largeOrders.sell_orders }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">净流入</span>
            <span class="summary-value" :class="largeOrders.net_flow >= 0 ? 'buy' : 'sell'">
              {{ largeOrders.net_flow >= 0 ? '+' : '' }}{{ largeOrders.net_flow?.toFixed(2) }}
            </span>
          </div>
        </div>

        <div class="direction-banner" :class="largeOrders.direction">
          {{ largeOrders.direction_label }}
        </div>

        <div class="orders-list">
          <h4>最近大单</h4>
          <div v-for="(order, idx) in largeOrders.large_orders?.slice(0, 10)" :key="idx" class="order-item" :class="order.side">
            <span class="order-side">{{ order.side === 'buy' ? '🟢 买入' : '🔴 卖出' }}</span>
            <span class="order-price">${{ order.price?.toLocaleString() }}</span>
            <span class="order-amount">{{ order.amount?.toFixed(4) }}</span>
            <span class="order-value">${{ order.value?.toLocaleString() }}</span>
            <span class="order-time">{{ formatTime(order.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 订单流分析 -->
    <div class="card">
      <h3>📊 订单流分析</h3>
      <div class="order-flow" v-if="orderFlow">
        <div class="flow-summary">
          <div class="flow-state" :class="orderFlow.flow_state">
            {{ orderFlow.flow_label }}
          </div>
        </div>

        <div class="flow-metrics">
          <div class="metric-item">
            <span class="metric-label">平均成交量</span>
            <span class="metric-value">{{ orderFlow.average_volume?.toFixed(0) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">成交量放大</span>
            <span class="metric-value">{{ orderFlow.volume_spike_ratio?.toFixed(2) }}x</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">订单不平衡</span>
            <span class="metric-value" :class="orderFlow.order_imbalance >= 0 ? 'positive' : 'negative'">
              {{ orderFlow.order_imbalance?.toFixed(3) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">买盘主导</span>
            <span class="metric-value">{{ (orderFlow.buy_dominance * 100)?.toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 庄家阶段识别 -->
    <div class="card">
      <h3>🎭 庄家阶段识别</h3>
      <div class="phase-analysis" v-if="manipulationPhase">
        <div class="phase-main">
          <div class="phase-label">{{ manipulationPhase.phase_label }}</div>
          <div class="phase-confidence">
            置信度: {{ (manipulationPhase.confidence * 100).toFixed(0) }}%
          </div>
        </div>

        <div class="phase-indicators">
          <div class="indicator-item">
            <span class="indicator-label">价格稳定性</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                :style="{ width: (manipulationPhase.indicators?.price_stability * 100) + '%' }"
              ></div>
            </div>
            <span class="indicator-value">{{ (manipulationPhase.indicators?.price_stability * 100).toFixed(0) }}%</span>
          </div>
          <div class="indicator-item">
            <span class="indicator-label">成交量确认</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                :style="{ width: (manipulationPhase.indicators?.volume_confirmation * 100) + '%' }"
              ></div>
            </div>
            <span class="indicator-value">{{ (manipulationPhase.indicators?.volume_confirmation * 100).toFixed(0) }}%</span>
          </div>
          <div class="indicator-item">
            <span class="indicator-label">趋势强度</span>
            <div class="indicator-bar">
              <div 
                class="indicator-fill" 
                :style="{ width: (manipulationPhase.indicators?.trend_strength * 100) + '%' }"
              ></div>
            </div>
            <span class="indicator-value">{{ (manipulationPhase.indicators?.trend_strength * 100).toFixed(0) }}%</span>
          </div>
        </div>

        <div class="phase-stats">
          <div class="stat-item">
            <span class="stat-label">价格波动</span>
            <span class="stat-value">{{ (manipulationPhase.price_range * 100).toFixed(1) }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">量比</span>
            <span class="stat-value">{{ manipulationPhase.volume_ratio?.toFixed(2) }}x</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">价格趋势</span>
            <span class="stat-value" :class="manipulationPhase.price_trend >= 0 ? 'positive' : 'negative'">
              {{ (manipulationPhase.price_trend * 100).toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 巨鲸预警 -->
    <div class="card" v-if="whaleAlerts && whaleAlerts.length > 0">
      <h3>⚠️ 巨鲸预警</h3>
      <div class="alerts-list">
        <div v-for="(alert, idx) in whaleAlerts" :key="idx" class="alert-item" :class="alert.level">
          <div class="alert-type">{{ alert.type }}</div>
          <div class="alert-title">{{ alert.title }}</div>
          <div class="alert-message">{{ alert.message }}</div>
          <div class="alert-suggestion">💡 {{ alert.suggestion }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const selectedSymbol = ref('BTCUSDT')
const whaleAnalysis = ref<any>(null)
const largeOrders = ref<any>(null)
const orderFlow = ref<any>(null)
const manipulationPhase = ref<any>(null)
const whaleAlerts = ref<any[]>([])

const apiBase = '/api'

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString('zh-CN')
}

const fetchWhaleAnalysis = async () => {
  try {
    const response = await fetch(`${apiBase}/whale-analysis/full/${selectedSymbol.value}`)
    whaleAnalysis.value = await response.json()
    largeOrders.value = whaleAnalysis.value.large_orders
    orderFlow.value = whaleAnalysis.value.order_flow
    manipulationPhase.value = whaleAnalysis.value.manipulation_phase
    whaleAlerts.value = whaleAnalysis.value.alerts || []
  } catch (error) {
    console.error('获取巨鲸分析失败:', error)
  }
}

const fetchLargeOrders = async () => {
  try {
    const response = await fetch(`${apiBase}/whale-analysis/large-orders/${selectedSymbol.value}`)
    largeOrders.value = await response.json()
  } catch (error) {
    console.error('获取大单数据失败:', error)
  }
}

const fetchOrderFlow = async () => {
  try {
    const response = await fetch(`${apiBase}/whale-analysis/order-flow/${selectedSymbol.value}`)
    orderFlow.value = await response.json()
  } catch (error) {
    console.error('获取订单流失败:', error)
  }
}

const fetchManipulationPhase = async () => {
  try {
    const response = await fetch(`${apiBase}/whale-analysis/phase/${selectedSymbol.value}`)
    manipulationPhase.value = await response.json()
  } catch (error) {
    console.error('获取庄家阶段失败:', error)
  }
}

const fetchAlerts = async () => {
  try {
    const response = await fetch(`${apiBase}/whale-analysis/alerts/${selectedSymbol.value}`)
    const data = await response.json()
    whaleAlerts.value = data.alerts || []
  } catch (error) {
    console.error('获取巨鲸预警失败:', error)
  }
}

const refreshAll = async () => {
  await fetchWhaleAnalysis()
}

onMounted(() => {
  refreshAll()
  setInterval(refreshAll, 30000) // 30秒刷新
})
</script>

<style scoped>
.whale-analysis {
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

.overall-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.overall-card.neutral {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
}

.overall-card.bullish {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.overall-card.bearish {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
}

.overall-main {
  display: flex;
  align-items: center;
  gap: 20px;
}

.overall-emoji {
  font-size: 56px;
}

.overall-info h3 {
  margin: 0 0 12px 0;
  color: white;
  font-size: 24px;
}

.overall-signals {
  display: flex;
  gap: 16px;
}

.signal {
  font-size: 14px;
  opacity: 0.95;
}

.orders-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.summary-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.summary-value.buy {
  color: #10b981;
}

.summary-value.sell {
  color: #ef4444;
}

.direction-banner {
  text-align: center;
  padding: 16px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.direction-banner.inflow {
  background: #d1fae5;
  color: #065f46;
}

.direction-banner.outflow {
  background: #fee2e2;
  color: #7f1d1d;
}

.direction-banner.neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.orders-list h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.order-item {
  display: grid;
  grid-template-columns: 100px 1fr 100px 120px 160px;
  gap: 12px;
  padding: 12px;
  background: #f8f9ff;
  border-radius: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.order-item.buy {
  border-left: 3px solid #10b981;
}

.order-item.sell {
  border-left: 3px solid #ef4444;
}

.order-side {
  font-weight: 600;
}

.order-price,
.order-amount,
.order-value,
.order-time {
  color: #666;
  font-size: 13px;
}

.flow-state {
  display: inline-block;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.flow-state.strong_buy,
.flow-state.moderate_buy {
  background: #d1fae5;
  color: #065f46;
}

.flow-state.strong_sell,
.flow-state.moderate_sell {
  background: #fee2e2;
  color: #7f1d1d;
}

.flow-state.balanced {
  background: #f3f4f6;
  color: #4b5563;
}

.flow-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.metric-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.metric-value.positive {
  color: #10b981;
}

.metric-value.negative {
  color: #ef4444;
}

.phase-main {
  text-align: center;
  padding: 20px;
  background: #f8f9ff;
  border-radius: 12px;
  margin-bottom: 20px;
}

.phase-label {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.phase-confidence {
  color: #666;
}

.phase-indicators {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.indicator-item {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  gap: 12px;
  align-items: center;
}

.indicator-label {
  color: #666;
}

.indicator-bar {
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.indicator-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.indicator-value {
  text-align: right;
  font-weight: 600;
  color: #333;
}

.phase-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.negative {
  color: #ef4444;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid;
}

.alert-item.warning {
  background: #fffbeb;
  border-color: #f59e0b;
}

.alert-item.info {
  background: #eff6ff;
  border-color: #3b82f6;
}

.alert-type {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.alert-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.alert-message {
  color: #666;
  margin-bottom: 8px;
}

.alert-suggestion {
  color: #667eea;
  font-size: 13px;
}

@media (max-width: 768px) {
  .orders-summary,
  .flow-metrics,
  .phase-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .order-item {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
}
</style>

