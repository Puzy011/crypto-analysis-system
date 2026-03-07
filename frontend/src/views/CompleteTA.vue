<template>
  <div class="complete-ta">
    <div class="page-header">
      <h1>📊 完整技术指标</h1>
      <p>100+ 技术指标，参考 TA-Lib、Pandas-TA</p>
    </div>

    <!-- 指标概览 -->
    <div class="card" v-if="latestIndicators">
      <h3>🎯 最新指标</h3>
      <div class="indicators-grid">
        <div 
          v-for="(value, key) in latestIndicators.indicators" 
          :key="key"
          class="indicator-card"
        >
          <span class="indicator-name">{{ formatIndicatorName(String(key)) }}</span>
          <span class="indicator-value" :class="getValueClass(String(key), value)">
            {{ formatIndicatorValue(String(key), value) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 趋势指标 -->
    <div class="card">
      <h3>📈 趋势指标</h3>
      <div class="ta-section">
        <div class="ta-item">
          <span class="ta-label">SMA (20)</span>
          <span class="ta-value" v-if="smaData">{{ smaData.latest?.toFixed(2) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">EMA (20)</span>
          <span class="ta-value" v-if="emaData">{{ emaData.latest?.toFixed(2) }}</span>
        </div>
        <div class="ta-item macd-item">
          <span class="ta-label">MACD</span>
          <div class="macd-values" v-if="macdData">
            <span class="macd-value">MACD: {{ macdData.latest_macd?.toFixed(4) }}</span>
            <span class="macd-value">Signal: {{ macdData.latest_signal?.toFixed(4) }}</span>
            <span class="macd-value">Hist: {{ macdData.latest_histogram?.toFixed(4) }}</span>
          </div>
        </div>
        <div class="ta-item bb-item">
          <span class="ta-label">布林带</span>
          <div class="bb-values" v-if="bbData">
            <span class="bb-value up">上: {{ bbData.upper?.[bbData.upper.length-1]?.toFixed(2) }}</span>
            <span class="bb-value mid">中: {{ bbData.middle?.[bbData.middle.length-1]?.toFixed(2) }}</span>
            <span class="bb-value low">下: {{ bbData.lower?.[bbData.lower.length-1]?.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 动量指标 -->
    <div class="card">
      <h3>⚡ 动量指标</h3>
      <div class="ta-section">
        <div class="ta-item rsi-item">
          <span class="ta-label">RSI (14)</span>
          <span 
            class="ta-value rsi-value" 
            :class="getRsiClass(rsiData?.latest)"
            v-if="rsiData"
          >
            {{ rsiData.latest?.toFixed(2) }}
          </span>
          <div class="rsi-meter" v-if="rsiData">
            <div class="rsi-scale">
              <span>0</span>
              <span>30</span>
              <span>50</span>
              <span>70</span>
              <span>100</span>
            </div>
            <div class="rsi-bar">
              <div 
                class="rsi-fill" 
                :class="getRsiClass(rsiData.latest)"
                :style="{ width: rsiData.latest + '%' }"
              ></div>
            </div>
            <div class="rsi-labels">
              <span class="oversold">超卖</span>
              <span class="overbought">超买</span>
            </div>
          </div>
        </div>
        <div class="ta-item">
          <span class="ta-label">Stochastic K</span>
          <span class="ta-value" v-if="stochData">{{ stochData.k?.[stochData.k.length-1]?.toFixed(2) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">Stochastic D</span>
          <span class="ta-value" v-if="stochData">{{ stochData.d?.[stochData.d.length-1]?.toFixed(2) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">CCI</span>
          <span class="ta-value" v-if="latestIndicators">{{ latestIndicators.indicators?.cci?.toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <!-- 成交量指标 -->
    <div class="card">
      <h3>📊 成交量指标</h3>
      <div class="ta-section">
        <div class="ta-item">
          <span class="ta-label">OBV</span>
          <span class="ta-value" v-if="latestIndicators">{{ formatLargeNumber(latestIndicators.indicators?.obv) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">AD</span>
          <span class="ta-value" v-if="latestIndicators">{{ formatLargeNumber(latestIndicators.indicators?.ad) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">MFI</span>
          <span class="ta-value" v-if="latestIndicators">{{ latestIndicators.indicators?.mfi?.toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <!-- 波动率指标 -->
    <div class="card">
      <h3>🌊 波动率指标</h3>
      <div class="ta-section">
        <div class="ta-item">
          <span class="ta-label">ATR</span>
          <span class="ta-value" v-if="latestIndicators">{{ latestIndicators.indicators?.atr?.toFixed(2) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">历史波动率</span>
          <span class="ta-value" v-if="latestIndicators">{{ (latestIndicators.indicators?.volatility * 100)?.toFixed(2) }}%</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">Williams %R</span>
          <span class="ta-value" v-if="latestIndicators">{{ latestIndicators.indicators?.williams_r?.toFixed(2) }}</span>
        </div>
        <div class="ta-item">
          <span class="ta-label">Awesome Oscillator</span>
          <span class="ta-value" v-if="latestIndicators">{{ latestIndicators.indicators?.ao?.toFixed(4) }}</span>
        </div>
      </div>
    </div>

    <!-- K线模式 -->
    <div class="card">
      <h3>🎯 K线模式识别</h3>
      <div class="pattern-section">
        <div class="pattern-item" :class="{ active: latestIndicators?.indicators?.is_doji }">
          <span class="pattern-icon">🕯️</span>
          <span class="pattern-name">十字星 (Doji)</span>
          <span class="pattern-status">
            {{ latestIndicators?.indicators?.is_doji ? '✅ 检测到' : '❌ 未检测到' }}
          </span>
        </div>
        <div class="pattern-item" :class="{ active: latestIndicators?.indicators?.is_hammer }">
          <span class="pattern-icon">🔨</span>
          <span class="pattern-name">锤子线 (Hammer)</span>
          <span class="pattern-status">
            {{ latestIndicators?.indicators?.is_hammer ? '✅ 检测到' : '❌ 未检测到' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 刷新按钮 -->
    <div class="refresh-section">
      <button @click="refreshAll" class="btn btn-primary" :disabled="isLoading">
        {{ isLoading ? '刷新中...' : '🔄 刷新指标' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const selectedSymbol = ref('BTCUSDT')
const isLoading = ref(false)
const latestIndicators = ref<any>(null)
const smaData = ref<any>(null)
const emaData = ref<any>(null)
const rsiData = ref<any>(null)
const macdData = ref<any>(null)
const bbData = ref<any>(null)
const stochData = ref<any>(null)

const apiBase = '/api'

const formatIndicatorName = (key: string) => {
  const names: Record<string, string> = {
    'sma_5': 'SMA 5',
    'sma_10': 'SMA 10',
    'sma_20': 'SMA 20',
    'sma_50': 'SMA 50',
    'sma_100': 'SMA 100',
    'sma_200': 'SMA 200',
    'ema_5': 'EMA 5',
    'ema_10': 'EMA 10',
    'ema_20': 'EMA 20',
    'ema_50': 'EMA 50',
    'ema_100': 'EMA 100',
    'ema_200': 'EMA 200',
    'macd': 'MACD',
    'macd_signal': 'MACD Signal',
    'macd_hist': 'MACD Hist',
    'bb_upper': 'BB Upper',
    'bb_middle': 'BB Middle',
    'bb_lower': 'BB Lower',
    'bb_bandwidth': 'BB Bandwidth',
    'bb_percent_b': 'BB %B',
    'rsi_7': 'RSI 7',
    'rsi_14': 'RSI 14',
    'rsi_21': 'RSI 21',
    'stoch_k': 'Stoch K',
    'stoch_d': 'Stoch D',
    'cci': 'CCI',
    'roc': 'ROC',
    'obv': 'OBV',
    'ad': 'AD',
    'mfi': 'MFI',
    'atr': 'ATR',
    'volatility': 'Volatility',
    'williams_r': 'Williams %R',
    'ao': 'AO',
    'is_doji': 'Doji',
    'is_hammer': 'Hammer'
  }
  return names[key] || key
}

const formatIndicatorValue = (_key: string, value: any) => {
  if (typeof value === 'boolean') {
    return value ? '✅' : '❌'
  }
  if (Math.abs(value) > 1000000) {
    return (value / 1000000).toFixed(2) + 'M'
  }
  if (Math.abs(value) > 1000) {
    return value.toFixed(0)
  }
  return value.toFixed(4)
}

const formatLargeNumber = (value: number) => {
  if (!value) return '0'
  if (Math.abs(value) > 1000000) {
    return (value / 1000000).toFixed(2) + 'M'
  }
  if (Math.abs(value) > 1000) {
    return (value / 1000).toFixed(2) + 'K'
  }
  return value.toFixed(0)
}

const getValueClass = (key: string, value: number) => {
  if (key.includes('rsi')) {
    if (value < 30) return 'oversold'
    if (value > 70) return 'overbought'
  }
  if (key.includes('macd_hist') || key.includes('ao')) {
    return value >= 0 ? 'positive' : 'negative'
  }
  return ''
}

const getRsiClass = (value: number) => {
  if (!value) return ''
  if (value < 30) return 'oversold'
  if (value > 70) return 'overbought'
  return 'neutral'
}

const fetchLatestIndicators = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/latest/${selectedSymbol.value}`)
    latestIndicators.value = await response.json()
  } catch (error) {
    console.error('获取最新指标失败:', error)
  }
}

const fetchSMA = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/sma/${selectedSymbol.value}?period=20`)
    smaData.value = await response.json()
  } catch (error) {
    console.error('获取 SMA 失败:', error)
  }
}

const fetchEMA = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/ema/${selectedSymbol.value}?period=20`)
    emaData.value = await response.json()
  } catch (error) {
    console.error('获取 EMA 失败:', error)
  }
}

const fetchRSI = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/rsi/${selectedSymbol.value}?period=14`)
    rsiData.value = await response.json()
  } catch (error) {
    console.error('获取 RSI 失败:', error)
  }
}

const fetchMACD = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/macd/${selectedSymbol.value}`)
    macdData.value = await response.json()
  } catch (error) {
    console.error('获取 MACD 失败:', error)
  }
}

const fetchBollinger = async () => {
  try {
    const response = await fetch(`${apiBase}/complete-ta/bollinger/${selectedSymbol.value}`)
    bbData.value = await response.json()
  } catch (error) {
    console.error('获取布林带失败:', error)
  }
}

const refreshAll = async () => {
  isLoading.value = true
  await Promise.all([
    fetchLatestIndicators(),
    fetchSMA(),
    fetchEMA(),
    fetchRSI(),
    fetchMACD(),
    fetchBollinger()
  ])
  isLoading.value = false
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.complete-ta {
  padding: 20px;
  max-width: 1400px;
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

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.indicator-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f8f9ff;
  border-radius: 8px;
}

.indicator-name {
  font-size: 12px;
  color: #666;
}

.indicator-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.indicator-value.oversold {
  color: #10b981;
}

.indicator-value.overbought {
  color: #ef4444;
}

.indicator-value.positive {
  color: #10b981;
}

.indicator-value.negative {
  color: #ef4444;
}

.ta-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.ta-item {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.ta-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.ta-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.macd-item,
.bb-item {
  grid-column: span 2;
}

.macd-values,
.bb-values {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.macd-value,
.bb-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.bb-value.up {
  color: #ef4444;
}

.bb-value.mid {
  color: #666;
}

.bb-value.low {
  color: #10b981;
}

.rsi-item {
  grid-column: span 2;
}

.rsi-value {
  font-size: 24px;
  margin-bottom: 12px;
}

.rsi-value.oversold {
  color: #10b981;
}

.rsi-value.overbought {
  color: #ef4444;
}

.rsi-value.neutral {
  color: #666;
}

.rsi-meter {
  margin-top: 8px;
}

.rsi-scale {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}

.rsi-bar {
  height: 12px;
  background: linear-gradient(90deg, #10b981 0%, #eab308 50%, #ef4444 100%);
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.rsi-fill {
  height: 100%;
  background: rgba(255,255,255,0.5);
  position: absolute;
  left: 0;
  top: 0;
  transition: width 0.3s;
}

.rsi-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 11px;
}

.rsi-labels .oversold {
  color: #10b981;
}

.rsi-labels .overbought {
  color: #ef4444;
}

.pattern-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.pattern-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
  border: 2px solid transparent;
}

.pattern-item.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #f8f9ff 0%, #e0e7ff 100%);
}

.pattern-icon {
  font-size: 28px;
}

.pattern-name {
  flex: 1;
  font-weight: 600;
  color: #333;
}

.pattern-status {
  font-size: 14px;
  color: #666;
}

.refresh-section {
  text-align: center;
  padding: 20px 0;
}

.btn {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
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

@media (max-width: 768px) {
  .macd-item,
  .bb-item,
  .rsi-item {
    grid-column: span 1;
  }
}
</style>

