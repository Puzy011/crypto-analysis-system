<template>
  <div class="comprehensive-sentiment">
    <div class="page-header">
      <h1>📰 综合舆情分析</h1>
      <p>FinBERT 风格金融情感分析 + 新闻-价格关联</p>
    </div>

    <div class="card control-card">
      <div class="controls">
        <div class="control-item">
          <span class="control-label">交易对</span>
          <select v-model="selectedSymbol" class="input-select">
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="BNBUSDT">BNB/USDT</option>
            <option value="SOLUSDT">SOL/USDT</option>
          </select>
        </div>
        <div class="control-item">
          <span class="control-label">预测窗口</span>
          <select v-model="forecastHours" class="input-select">
            <option :value="6">6小时</option>
            <option :value="12">12小时</option>
            <option :value="24">24小时</option>
            <option :value="48">48小时</option>
          </select>
        </div>
      </div>
    </div>

    <div class="card scheduler-card" v-if="schedulerStatus">
      <h3>⏱ 调度状态</h3>
      <div class="sentiment-index-summary">
        <div class="summary-item">
          <span class="summary-label">运行状态</span>
          <span class="summary-value" :class="schedulerStatus.running ? 'positive' : 'negative'">
            {{ schedulerStatus.running ? '运行中' : '已停止' }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">采集间隔</span>
          <span class="summary-value">{{ schedulerStatus.interval_seconds }}s</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">最近调度</span>
          <span class="summary-value">{{ formatIso(schedulerStatus.last_run_at) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">错误状态</span>
          <span class="summary-value">{{ schedulerStatus.last_error || '无' }}</span>
        </div>
      </div>
    </div>

    <!-- 快速刷新 -->
    <div class="refresh-section">
      <button @click="refreshAll" class="btn btn-primary" :disabled="isLoading">
        {{ isLoading ? '⏳ 刷新中...' : '🔄 刷新数据' }}
      </button>
      <button @click="triggerCollection" class="btn btn-secondary" :disabled="isCollecting">
        {{ isCollecting ? '⏳ 采集中...' : '📥 手动采集' }}
      </button>
    </div>

    <!-- 综合舆情概览 -->
    <div class="card overview-card" v-if="fullAnalysis">
      <h3>🎯 综合舆情概览</h3>
      <div class="sentiment-index-summary">
        <div class="summary-item">
          <span class="summary-label">恐惧贪婪指数</span>
          <span class="summary-value" :class="getFgClass(fullAnalysis.sentiment_index?.fear_greed_index)">
            {{ fullAnalysis.sentiment_index?.fear_greed_index?.toFixed(1) }}
            {{ fullAnalysis.sentiment_index?.market_state_emoji }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">市场状态</span>
          <span class="summary-value">{{ fullAnalysis.sentiment_index?.market_state }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">平均情感分</span>
          <span class="summary-value" :class="fullAnalysis.sentiment_index?.avg_sentiment_score >= 0 ? 'positive' : 'negative'">
            {{ fullAnalysis.sentiment_index?.avg_sentiment_score?.toFixed(2) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">分析新闻数</span>
          <span class="summary-value">{{ fullAnalysis.news_count }}</span>
        </div>
      </div>
    </div>

    <!-- 多平台贡献 -->
    <div class="card" v-if="fullAnalysis?.multi_platform?.platform_breakdown">
      <h3>🌐 多平台舆情贡献</h3>
      <div class="sentiment-index-summary">
        <div class="summary-item">
          <span class="summary-label">综合分</span>
          <span class="summary-value" :class="fullAnalysis.multi_platform.overall_sentiment_score >= 0 ? 'positive' : 'negative'">
            {{ fullAnalysis.multi_platform.overall_sentiment_score?.toFixed(3) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">恐惧贪婪</span>
          <span class="summary-value">{{ fullAnalysis.multi_platform.fear_greed_index?.toFixed(1) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">采集条数</span>
          <span class="summary-value">{{ fullAnalysis.multi_platform.total_items }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">质量评分</span>
          <span class="summary-value">
            {{ ((fullAnalysis.multi_platform.data_quality?.quality_score || 0) * 100).toFixed(0) }}%
          </span>
        </div>
      </div>

      <div class="platform-grid">
        <div
          v-for="(stats, platform) in fullAnalysis.multi_platform.platform_breakdown"
          :key="platform"
          class="platform-card"
        >
          <div class="platform-name">{{ getPlatformName(String(platform)) }}</div>
          <div class="platform-metric">样本: {{ stats.count }}</div>
          <div class="platform-metric">均值: {{ stats.avg_sentiment?.toFixed(3) }}</div>
          <div class="platform-metric">加权: {{ stats.weighted_sentiment?.toFixed(3) }}</div>
          <div class="platform-metric">多头占比: {{ ((stats.positive_ratio || 0) * 100).toFixed(0) }}%</div>
        </div>
      </div>
    </div>

    <!-- 时间趋势 -->
    <div class="card" v-if="fullAnalysis?.time_analysis?.windows">
      <h3>⏳ 时间趋势分析</h3>
      <div class="window-grid">
        <div v-for="(metrics, key) in fullAnalysis.time_analysis.windows" :key="key" class="window-card">
          <div class="window-title">{{ String(key).toUpperCase() }}</div>
          <div class="window-row">趋势: {{ getWindowTrendName(metrics.trend_label) }}</div>
          <div class="window-row">斜率/h: {{ formatSigned(metrics.slope_per_hour) }}</div>
          <div class="window-row">动量: {{ formatSigned(metrics.momentum) }}</div>
          <div class="window-row">波动: {{ metrics.volatility?.toFixed(3) }}</div>
          <div class="window-row">关注度: {{ metrics.avg_attention?.toFixed(1) }}</div>
        </div>
      </div>

      <div class="burst-row" v-if="fullAnalysis.time_analysis.burst">
        <span class="summary-label">突发检测:</span>
        <span class="summary-value" :class="fullAnalysis.time_analysis.burst.is_spike ? 'negative' : 'neutral'">
          score {{ fullAnalysis.time_analysis.burst.score?.toFixed(2) }}
          · {{ fullAnalysis.time_analysis.burst.is_spike ? '检测到情绪突发' : '无明显突发' }}
        </span>
      </div>

      <div class="timeline-preview" v-if="timelinePreview.length">
        <div class="timeline-head">
          <span>时间</span>
          <span>综合分</span>
          <span>消息量</span>
        </div>
        <div v-for="point in timelinePreview" :key="point.timestamp" class="timeline-row">
          <span>{{ formatTime(point.timestamp) }}</span>
          <span :class="point.overall_sentiment_score >= 0 ? 'positive' : 'negative'">
            {{ point.overall_sentiment_score?.toFixed(3) }}
          </span>
          <span>{{ point.total_items }}</span>
        </div>
      </div>
    </div>

    <!-- 趋势预测 -->
    <div class="card" v-if="fullAnalysis?.trend_forecast">
      <h3>📈 舆情趋势预测</h3>
      <div class="sentiment-index-summary">
        <div class="summary-item">
          <span class="summary-label">预测方向</span>
          <span class="summary-value" :class="getTrendClass(fullAnalysis.trend_forecast.direction)">
            {{ fullAnalysis.trend_forecast.direction_label }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">预测分值</span>
          <span class="summary-value" :class="fullAnalysis.trend_forecast.forecast_score >= 0 ? 'positive' : 'negative'">
            {{ fullAnalysis.trend_forecast.forecast_score?.toFixed(3) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">预期恐惧贪婪</span>
          <span class="summary-value">
            {{ fullAnalysis.trend_forecast.expected_fear_greed_index?.toFixed(1) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">预测置信度</span>
          <span class="summary-value">
            {{ (fullAnalysis.trend_forecast.confidence * 100).toFixed(1) }}%
          </span>
        </div>
      </div>
      <div class="news-keywords" v-if="fullAnalysis.trend_forecast.drivers?.length">
        <span class="keywords-label">驱动因子:</span>
        <span
          v-for="(driver, idx) in fullAnalysis.trend_forecast.drivers"
          :key="idx"
          class="news-keyword"
        >
          {{ driver }}
        </span>
      </div>
    </div>

    <!-- 数据质量与事件分布 -->
    <div class="card" v-if="fullAnalysis?.sentiment_index">
      <h3>🧩 数据质量</h3>
      <div class="sentiment-index-summary">
        <div class="summary-item">
          <span class="summary-label">来源多样性</span>
          <span class="summary-value">
            {{ ((fullAnalysis.sentiment_index.source_diversity_score || 0) * 100).toFixed(0) }}%
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">24h 动量</span>
          <span class="summary-value" :class="fullAnalysis.sentiment_index.momentum_24h >= 0 ? 'positive' : 'negative'">
            {{ (fullAnalysis.sentiment_index.momentum_24h || 0).toFixed(3) }}
          </span>
        </div>
      </div>
      <div class="news-keywords" v-if="fullAnalysis.sentiment_index.hot_topics?.length">
        <span class="keywords-label">热词:</span>
        <span v-for="(kw, idx) in fullAnalysis.sentiment_index.hot_topics" :key="idx" class="news-keyword">
          {{ kw }}
        </span>
      </div>
      <div class="entities" v-if="fullAnalysis.sentiment_index.event_distribution">
        <div v-for="(count, evt) in fullAnalysis.sentiment_index.event_distribution" :key="evt" class="entity-group">
          <span class="entity-type">{{ evt }}</span>
          <span class="entity-value">{{ count }}</span>
        </div>
      </div>
    </div>

    <!-- 关键词展示 -->
    <div class="card keywords-card" v-if="fullAnalysis?.keywords">
      <h3>🔑 关键词分析</h3>
      
      <div class="keywords-section">
        <div class="keywords-type">
          <h4>TF-IDF 关键词</h4>
          <div class="keywords-list">
            <div 
              v-for="(kw, idx) in fullAnalysis.keywords?.tfidf?.slice(0, 10)" 
              :key="idx"
              class="keyword-item"
            >
              <span class="keyword-word">{{ kw.word }}</span>
              <span class="keyword-score">{{ kw.score?.toFixed(4) }}</span>
            </div>
          </div>
        </div>
        
        <div class="keywords-type">
          <h4>TextRank 关键词</h4>
          <div class="keywords-list">
            <div 
              v-for="(kw, idx) in fullAnalysis.keywords?.textrank?.slice(0, 10)" 
              :key="idx"
              class="keyword-item"
            >
              <span class="keyword-word">{{ kw.word }}</span>
              <span class="keyword-score">{{ kw.score?.toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最新新闻列表 -->
    <div class="card news-card" v-if="fullAnalysis?.news">
      <h3>📰 最新新闻</h3>
      <div class="news-list">
        <div v-for="news in fullAnalysis.news?.slice(0, 10)" :key="news.id" class="news-item">
          <div class="news-header">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ formatTime(news.timestamp) }}</span>
          </div>
          <div class="news-title">{{ news.title }}</div>
          
          <div class="news-sentiment" v-if="news.enhanced_sentiment">
            <div class="sentiment-score">
              <span class="sentiment-label">情感评分:</span>
              <span 
                class="sentiment-value" 
                :class="getSentimentClass(news.enhanced_sentiment.sentiment_score)"
              >
                {{ news.enhanced_sentiment.sentiment_score?.toFixed(2) }}
              </span>
            </div>
            
            <div class="matched-words" v-if="news.enhanced_sentiment.matched_words?.length > 0">
              <span class="matched-label">匹配词:</span>
              <span 
                v-for="(word, idx) in news.enhanced_sentiment.matched_words" 
                :key="idx"
                class="matched-word"
              >
                {{ word[0] }} ({{ word[1] }})
              </span>
            </div>
            
            <div class="news-keywords" v-if="news.enhanced_sentiment.keywords?.length > 0">
              <span class="keywords-label">关键词:</span>
              <span 
                v-for="(kw, idx) in news.enhanced_sentiment.keywords?.slice(0, 5)" 
                :key="idx"
                class="news-keyword"
              >
                {{ kw }}
              </span>
            </div>
            
            <div class="entities" v-if="news.enhanced_sentiment.entities">
              <div 
                v-for="(entityList, entityType) in news.enhanced_sentiment.entities" 
                :key="entityType"
                class="entity-group"
              >
                <span class="entity-type">{{ getEntityTypeName(String(entityType)) }}:</span>
                <span v-for="(entity, idx) in entityList" :key="idx" class="entity-value">
                  {{ entity }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const isLoading = ref(false)
const isCollecting = ref(false)
const fullAnalysis = ref<any>(null)
const schedulerStatus = ref<any>(null)
const timelinePreview = ref<any[]>([])
const selectedSymbol = ref('BTCUSDT')
const forecastHours = ref(24)

const apiBase = '/api'

const formatTime = (ts: number) => {
  if (!ts) return '-'
  return new Date(ts).toLocaleString('zh-CN')
}

const formatIso = (value?: string) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const formatSigned = (value: number) => {
  if (!Number.isFinite(value)) return '0.000'
  return `${value >= 0 ? '+' : ''}${value.toFixed(3)}`
}

const getFgClass = (value: number) => {
  if (!value) return ''
  if (value < 25) return 'extreme_fear'
  if (value < 45) return 'fear'
  if (value < 55) return 'neutral'
  if (value < 75) return 'greed'
  return 'extreme_greed'
}

const getSentimentClass = (score: number) => {
  if (!score) return 'neutral'
  if (score > 0.5) return 'very_positive'
  if (score > 0.1) return 'positive'
  if (score < -0.5) return 'very_negative'
  if (score < -0.1) return 'negative'
  return 'neutral'
}

const getEntityTypeName = (type: string) => {
  const names: Record<string, string> = {
    'exchange': '交易所',
    'coin': '币种',
    'person': '人物',
    'event': '事件',
    'regulation': '监管'
  }
  return names[type] || type
}

const getTrendClass = (direction: string) => {
  if (direction === 'up') return 'positive'
  if (direction === 'down') return 'negative'
  return 'neutral'
}

const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    news: '新闻源',
    reddit: 'Reddit',
    announcement: '交易所公告'
  }
  return names[platform] || platform
}

const getWindowTrendName = (trend: string) => {
  const names: Record<string, string> = {
    up_fast: '快速升温',
    up: '升温',
    down_fast: '快速降温',
    down: '降温',
    sideways: '平稳',
    insufficient_data: '数据不足'
  }
  return names[trend] || trend
}

const fetchSchedulerStatus = async () => {
  try {
    const response = await fetch(`${apiBase}/comprehensive-sentiment/scheduler-status`)
    if (!response.ok) return
    const data = await response.json()
    schedulerStatus.value = data?.status || null
  } catch (error) {
    console.error('获取调度状态失败:', error)
  }
}

const fetchTimelinePreview = async () => {
  try {
    const response = await fetch(
      `${apiBase}/comprehensive-sentiment/timeline/${selectedSymbol.value}?hours=24&limit=12`
    )
    if (!response.ok) return
    const data = await response.json()
    timelinePreview.value = data?.timeline || []
  } catch (error) {
    console.error('获取时间线失败:', error)
  }
}

const refreshAll = async () => {
  isLoading.value = true
  try {
    const response = await fetch(
      `${apiBase}/comprehensive-sentiment/full-analysis/${selectedSymbol.value}?forecast_hours=${forecastHours.value}`
    )
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    fullAnalysis.value = await response.json()
    await Promise.all([fetchSchedulerStatus(), fetchTimelinePreview()])
  } catch (error) {
    console.error('获取综合舆情失败:', error)
  } finally {
    isLoading.value = false
  }
}

const triggerCollection = async () => {
  isCollecting.value = true
  try {
    const response = await fetch(
      `${apiBase}/comprehensive-sentiment/collect/${selectedSymbol.value}`,
      { method: 'POST' }
    )
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    await refreshAll()
  } catch (error) {
    console.error('手动采集失败:', error)
  } finally {
    isCollecting.value = false
  }
}

onMounted(() => {
  refreshAll()
})

watch([selectedSymbol, forecastHours], () => {
  refreshAll()
})
</script>

<style scoped>
.comprehensive-sentiment {
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

.refresh-section {
  text-align: center;
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
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
  font-size: 15px;
}

.control-card {
  background: #f8f9ff;
}

.scheduler-card {
  background: #eef6ff;
}

.controls {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
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

.input-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  min-width: 150px;
}

.sentiment-index-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-item {
  text-align: center;
  padding: 20px;
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
  font-size: 22px;
  font-weight: bold;
  color: #333;
}

.summary-value.positive {
  color: #10b981;
}

.summary-value.negative {
  color: #ef4444;
}

.summary-value.extreme_fear,
.summary-value.fear {
  color: #ef4444;
}

.summary-value.extreme_greed,
.summary-value.greed {
  color: #10b981;
}

.summary-value.neutral {
  color: #6b7280;
}

.keywords-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.keywords-type {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.keywords-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keyword-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
}

.keyword-word {
  font-weight: 500;
  color: #333;
}

.keyword-score {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.news-item {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.news-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.news-source {
  font-weight: 600;
  color: #667eea;
  font-size: 13px;
}

.news-time {
  color: #999;
  font-size: 12px;
}

.news-title {
  color: #333;
  margin-bottom: 12px;
  line-height: 1.5;
}

.news-sentiment {
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.sentiment-score {
  margin-bottom: 8px;
}

.sentiment-label {
  color: #666;
  font-size: 13px;
  margin-right: 8px;
}

.sentiment-value {
  font-weight: 600;
  font-family: monospace;
}

.sentiment-value.very_positive,
.sentiment-value.positive {
  color: #10b981;
}

.sentiment-value.very_negative,
.sentiment-value.negative {
  color: #ef4444;
}

.sentiment-value.neutral {
  color: #666;
}

.matched-words,
.news-keywords,
.entities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.matched-label,
.keywords-label {
  font-size: 12px;
  color: #666;
  margin-right: 4px;
}

.matched-word,
.news-keyword,
.entity-value {
  padding: 4px 10px;
  background: white;
  border-radius: 12px;
  font-size: 12px;
  color: #333;
}

.entity-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.entity-type {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
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
  background: #0f172a;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
}

.platform-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.platform-card {
  background: #f8f9ff;
  border-radius: 10px;
  padding: 12px;
}

.platform-name {
  font-weight: 700;
  margin-bottom: 8px;
  color: #111827;
}

.platform-metric {
  font-size: 13px;
  color: #374151;
  margin-bottom: 4px;
}

.window-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.window-card {
  background: #f8f9ff;
  border-radius: 10px;
  padding: 12px;
}

.window-title {
  font-weight: 700;
  margin-bottom: 8px;
}

.window-row {
  font-size: 13px;
  margin-bottom: 4px;
  color: #334155;
}

.burst-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.timeline-preview {
  margin-top: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}

.timeline-head,
.timeline-row {
  display: grid;
  grid-template-columns: 1.8fr 1fr 0.8fr;
  gap: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.timeline-head {
  background: #f3f4f6;
  font-weight: 600;
  color: #111827;
}

.timeline-row {
  border-top: 1px solid #f1f5f9;
}

@media (max-width: 768px) {
  .keywords-section {
    grid-template-columns: 1fr;
  }
}
</style>

