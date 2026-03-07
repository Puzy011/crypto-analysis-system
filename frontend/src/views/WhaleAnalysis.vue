<template>
  <div class="whale-analysis">
    <div class="page-header">
      <h1>🐋 巨鲸/庄家分析</h1>
      <p>OrderFlow 风格订单流分析 + 大单检测 + 庄家阶段识别</p>
    </div>

    <!-- 控制面板 -->
    <div class="card control-card">
      <div class="control-grid">
        <div class="control-item">
          <span class="control-label">交易对</span>
          <el-select v-model="selectedSymbol" filterable style="width: 220px;">
            <el-option label="BTC/USDT" value="BTCUSDT" />
            <el-option label="ETH/USDT" value="ETHUSDT" />
            <el-option label="BNB/USDT" value="BNBUSDT" />
            <el-option label="SOL/USDT" value="SOLUSDT" />
            <el-option label="XRP/USDT" value="XRPUSDT" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="control-label">模式</span>
          <el-radio-group v-model="tradeType" size="small">
            <el-radio-button label="realtime">实时</el-radio-button>
            <el-radio-button label="intraday">日内</el-radio-button>
            <el-radio-button label="longterm">长线</el-radio-button>
          </el-radio-group>
        </div>
        <div class="control-item">
          <el-button type="primary" @click="refreshAll">刷新分析</el-button>
        </div>
      </div>
      <div class="mode-note">
        当前模式: {{ whaleAnalysis?.trade_type_label || tradeTypeLabel }}
      </div>
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

    <!-- 主力结论（aice100 风格） -->
    <div class="card" v-if="whaleAnalysis">
      <h3>🧭 主力结论</h3>
      <div class="aice-summary-grid">
        <div class="summary-block">
          <div class="summary-title">庄家方向</div>
          <div class="summary-text">{{ whaleAnalysis.whale_direction || '暂无' }}</div>
        </div>
        <div class="summary-block">
          <div class="summary-title">庄家动作</div>
          <div class="summary-text">{{ whaleAnalysis.whale_action || '暂无' }}</div>
        </div>
        <div class="summary-block">
          <div class="summary-title">风险控制</div>
          <div class="summary-text" :class="riskClass(whaleAnalysis.risk_control)">
            {{ whaleAnalysis.risk_control || '中风险' }}
          </div>
        </div>
      </div>
      <div class="aice-advice">
        <span class="advice-label">交易建议:</span>
        <span>{{ whaleAnalysis.trade_advice || '等待更清晰信号' }}</span>
      </div>
      <div class="aice-summary-text" v-if="whaleAnalysis.summary">
        {{ whaleAnalysis.summary }}
      </div>
    </div>

    <!-- 数据可信度 -->
    <div class="card" v-if="whaleAnalysis?.data_quality">
      <h3>🛡️ 数据可信度</h3>
      <div class="smart-grid">
        <div class="smart-item">
          <span>可信度评分</span>
          <strong>{{ ((whaleAnalysis.data_quality.quality_score || 0) * 100).toFixed(0) }}%</strong>
        </div>
        <div class="smart-item">
          <span>可信等级</span>
          <strong>{{ whaleAnalysis.data_quality.quality_label }}</strong>
        </div>
        <div class="smart-item">
          <span>成交样本</span>
          <strong>{{ whaleAnalysis.data_quality.sources?.agg_trades?.count || 0 }}</strong>
        </div>
        <div class="smart-item">
          <span>盘口深度档位</span>
          <strong>{{ whaleAnalysis.data_quality.sources?.order_book?.depth_levels || 0 }}</strong>
        </div>
      </div>
      <div class="signal-points">
        <div class="signal-point">K线: {{ whaleAnalysis.data_quality.sources?.kline?.bars || 0 }} 根</div>
        <div class="signal-point">聚合成交: {{ whaleAnalysis.data_quality.sources?.agg_trades?.enabled ? '已接入' : '未接入' }}</div>
        <div class="signal-point">订单簿: {{ whaleAnalysis.data_quality.sources?.order_book?.enabled ? '已接入' : '未接入' }}</div>
        <div class="signal-point">合约指标: {{ whaleAnalysis.data_quality.sources?.derivatives?.enabled ? '已接入' : '未接入' }}</div>
      </div>
    </div>

    <!-- 合约指标 -->
    <div class="card" v-if="whaleAnalysis?.derivatives">
      <h3>📐 合约偏离指标</h3>
      <div class="smart-grid">
        <div class="smart-item">
          <span>资金费率</span>
          <strong>{{ ((whaleAnalysis.derivatives.funding_rate || 0) * 100).toFixed(4) }}%</strong>
        </div>
        <div class="smart-item">
          <span>全市场多空比</span>
          <strong>{{ (whaleAnalysis.derivatives.long_short_ratio || 0).toFixed(3) }}</strong>
        </div>
        <div class="smart-item">
          <span>Open Interest</span>
          <strong>{{ formatToMillions(whaleAnalysis.derivatives.open_interest) }}M</strong>
        </div>
        <div class="smart-item">
          <span>OI变化</span>
          <strong :class="(whaleAnalysis.derivatives.open_interest_change_pct || 0) >= 0 ? 'positive' : 'negative'">
            {{ ((whaleAnalysis.derivatives.open_interest_change_pct || 0) * 100).toFixed(2) }}%
          </strong>
        </div>
      </div>
    </div>

    <!-- 聪明钱分布 -->
    <div class="card" v-if="smartMoney">
      <h3>🐋 聪明钱分布</h3>
      <div class="smart-grid">
        <div class="smart-item">
          <span>总仓位价值</span>
          <strong>{{ (smartMoney.total_positions_m || 0).toFixed(2) }}M</strong>
        </div>
        <div class="smart-item">
          <span>多空比</span>
          <strong>{{ (smartMoney.long_short_ratio_percent || 0).toFixed(2) }}%</strong>
        </div>
        <div class="smart-item">
          <span>巨鲸强度</span>
          <strong>{{ (smartMoney.whale_strength || 0).toFixed(0) }}</strong>
        </div>
        <div class="smart-item">
          <span>总交易员</span>
          <strong>{{ smartMoney.total_traders || 0 }}</strong>
        </div>
      </div>
      <div class="smart-grid">
        <div class="smart-item buy-bg">
          <span>多头仓位</span>
          <strong>{{ (smartMoney.long_positions_m || 0).toFixed(2) }}M</strong>
        </div>
        <div class="smart-item sell-bg">
          <span>空头仓位</span>
          <strong>{{ (smartMoney.short_positions_m || 0).toFixed(2) }}M</strong>
        </div>
        <div class="smart-item buy-bg">
          <span>多头巨鲸</span>
          <strong>{{ smartMoney.long_whales || 0 }}</strong>
        </div>
        <div class="smart-item sell-bg">
          <span>空头巨鲸</span>
          <strong>{{ smartMoney.short_whales || 0 }}</strong>
        </div>
      </div>
    </div>

    <!-- 信号解读 -->
    <div class="card" v-if="signalExplanation.length > 0">
      <h3>🔍 信号解读</h3>
      <div class="signal-points">
        <div v-for="(point, idx) in signalExplanation" :key="idx" class="signal-point">
          {{ point }}
        </div>
      </div>
      <div class="extreme-list" v-if="whaleAnalysis?.extreme_30day?.length">
        <h4>近期极端情况</h4>
        <div v-for="(evt, idx) in whaleAnalysis.extreme_30day" :key="idx" class="extreme-item">
          {{ evt }}
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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

type TradeType = 'realtime' | 'intraday' | 'longterm'

const selectedSymbol = ref('BTCUSDT')
const tradeType = ref<TradeType>('realtime')
const whaleAnalysis = ref<any>(null)
const largeOrders = ref<any>(null)
const orderFlow = ref<any>(null)
const manipulationPhase = ref<any>(null)
const whaleAlerts = ref<any[]>([])
const smartMoney = ref<any>(null)
const signalExplanation = ref<string[]>([])
let refreshTimer: number | null = null

const apiBase = '/api'

const tradeTypeLabel = computed(() => {
  if (tradeType.value === 'realtime') return '实时短线'
  if (tradeType.value === 'intraday') return '日内波段'
  return '中长线'
})

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString('zh-CN')
}

const formatToMillions = (value: number) => {
  if (!value) return '0.00'
  return (value / 1_000_000).toFixed(2)
}

const riskClass = (risk: string) => {
  if (!risk) return ''
  if (risk.includes('高')) return 'risk-high'
  if (risk.includes('中')) return 'risk-mid'
  return 'risk-low'
}

const fetchWhaleAnalysis = async () => {
  try {
    const response = await fetch(
      `${apiBase}/whale-analysis/full/${selectedSymbol.value}?trade_type=${tradeType.value}`
    )
    whaleAnalysis.value = await response.json()
    largeOrders.value = whaleAnalysis.value.large_orders
    orderFlow.value = whaleAnalysis.value.order_flow
    manipulationPhase.value = whaleAnalysis.value.manipulation_phase
    whaleAlerts.value = whaleAnalysis.value.alerts || []
    smartMoney.value = whaleAnalysis.value.smart_money || null
    signalExplanation.value = whaleAnalysis.value.signal_explanation || []
  } catch (error) {
    console.error('获取巨鲸分析失败:', error)
  }
}

const refreshAll = async () => {
  await fetchWhaleAnalysis()
}

const getRefreshInterval = () => {
  if (tradeType.value === 'realtime') return 30000
  if (tradeType.value === 'intraday') return 60000
  return 120000
}

const startAutoRefresh = () => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
  refreshTimer = window.setInterval(refreshAll, getRefreshInterval())
}

watch([selectedSymbol, tradeType], async () => {
  await refreshAll()
  startAutoRefresh()
})

onMounted(async () => {
  await refreshAll()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
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

.control-card {
  background: #f8f9ff;
}

.control-grid {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
}

.mode-note {
  margin-top: 10px;
  color: #4b5563;
  font-size: 13px;
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

.aice-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.summary-block {
  background: #f8f9ff;
  border-radius: 10px;
  padding: 12px;
}

.summary-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.summary-text {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.summary-text.risk-high {
  color: #ef4444;
}

.summary-text.risk-mid {
  color: #f59e0b;
}

.summary-text.risk-low {
  color: #10b981;
}

.aice-advice {
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
}

.advice-label {
  font-weight: 600;
  margin-right: 8px;
}

.aice-summary-text {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.6;
}

.smart-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.smart-item {
  background: #f8f9ff;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.smart-item span {
  font-size: 12px;
  color: #6b7280;
}

.smart-item strong {
  color: #111827;
  font-size: 16px;
}

.smart-item.buy-bg {
  background: #ecfdf5;
}

.smart-item.sell-bg {
  background: #fef2f2;
}

.signal-points {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.signal-point {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  border-radius: 8px;
  padding: 10px 12px;
  color: #1f2937;
  font-size: 13px;
}

.extreme-list {
  margin-top: 14px;
}

.extreme-list h4 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 14px;
}

.extreme-item {
  font-size: 12px;
  color: #4b5563;
  margin-bottom: 6px;
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
  .aice-summary-grid,
  .smart-grid,
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

