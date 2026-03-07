<template>
  <div class="enhanced-sentiment">
    <div class="page-header">
      <h1>📰 增强舆情分析</h1>
      <p>FinBERT 风格情感分析 + 恐惧贪婪指数</p>
    </div>

    <!-- 恐惧贪婪指数 -->
    <div class="card fear-greed-card">
      <h3>🎢 恐惧贪婪指数</h3>
      <div class="fear-greed-main" v-if="fearGreed">
        <div class="fear-greed-meter">
          <div class="meter-scale">
            <span class="scale-label">极度恐惧</span>
            <span class="scale-label">恐惧</span>
            <span class="scale-label">中性</span>
            <span class="scale-label">贪婪</span>
            <span class="scale-label">极度贪婪</span>
          </div>
          <div class="meter-bar">
            <div 
              class="meter-fill" 
              :class="fearGreed.market_state"
              :style="{ width: fearGreed.fear_greed_index + '%' }"
            ></div>
            <div 
              class="meter-pointer" 
              :style="{ left: fearGreed.fear_greed_index + '%' }"
            ></div>
          </div>
        </div>
        <div class="fear-greed-value">
          <span class="value-number">{{ fearGreed.fear_greed_index.toFixed(1) }}</span>
          <span class="value-emoji">{{ fearGreed.market_state_emoji }}</span>
          <span class="value-label">{{ fearGreed.market_state }}</span>
        </div>
      </div>
    </div>

    <!-- 舆情指数 -->
    <div class="card">
      <h3>📊 综合舆情指数</h3>
      <div class="sentiment-overview" v-if="sentimentIndex">
        <div class="overview-grid">
          <div class="overview-item">
            <span class="overview-label">平均情感分</span>
            <span class="overview-value" :class="sentimentIndex.avg_sentiment_score > 0 ? 'positive' : 'negative'">
              {{ sentimentIndex.avg_sentiment_score.toFixed(2) }}
            </span>
          </div>
          <div class="overview-item">
            <span class="overview-label">多空比例</span>
            <span class="overview-value">
              {{ (sentimentIndex.bull_bear_ratio * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="overview-item">
            <span class="overview-label">分析新闻</span>
            <span class="overview-value">{{ sentimentIndex.news_analyzed }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">社交热度</span>
            <span class="overview-value">{{ sentimentIndex.social_volume?.toLocaleString() }}</span>
          </div>
        </div>

        <!-- 情感分布 -->
        <div class="sentiment-distribution" v-if="sentimentIndex.sentiment_distribution">
          <h4>情感分布</h4>
          <div class="distribution-bars">
            <div class="dist-item">
              <span class="dist-label">正面</span>
              <div class="dist-bar">
                <div 
                  class="dist-fill positive" 
                  :style="{ width: (sentimentIndex.sentiment_distribution.positive / totalNews * 100) + '%' }"
                ></div>
              </div>
              <span class="dist-count">{{ sentimentIndex.sentiment_distribution.positive || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">中性</span>
              <div class="dist-bar">
                <div 
                  class="dist-fill neutral" 
                  :style="{ width: (sentimentIndex.sentiment_distribution.neutral / totalNews * 100) + '%' }"
                ></div>
              </div>
              <span class="dist-count">{{ sentimentIndex.sentiment_distribution.neutral || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">负面</span>
              <div class="dist-bar">
                <div 
                  class="dist-fill negative" 
                  :style="{ width: (sentimentIndex.sentiment_distribution.negative / totalNews * 100) + '%' }"
                ></div>
              </div>
              <span class="dist-count">{{ sentimentIndex.sentiment_distribution.negative || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最新新闻 -->
    <div class="card">
      <h3>📰 最新新闻</h3>
      <div class="news-list" v-if="newsList.length > 0">
        <div v-for="news in newsList" :key="news.id" class="news-item">
          <div class="news-header">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ formatTime(news.timestamp) }}</span>
          </div>
          <div class="news-title">{{ news.title }}</div>
          <div class="news-sentiment" v-if="news.sentiment_analysis">
            <span 
              class="sentiment-tag" 
              :class="news.sentiment_analysis.sentiment_label"
            >
              {{ sentimentLabelText(news.sentiment_analysis.sentiment_label) }}
            </span>
            <span class="sentiment-score">
              置信度: {{ (news.sentiment_analysis.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="news-topics" v-if="news.sentiment_analysis?.topics">
            <span 
              v-for="topic in news.sentiment_analysis.topics" 
              :key="topic"
              class="topic-tag"
            >
              {{ topic }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 舆情预警 -->
    <div class="card" v-if="sentimentAlerts && sentimentAlerts.length > 0">
      <h3>⚠️ 舆情预警</h3>
      <div class="alerts-list">
        <div v-for="(alert, idx) in sentimentAlerts" :key="idx" class="alert-item" :class="alert.level">
          <div class="alert-title">{{ alert.title }}</div>
          <div class="alert-message">{{ alert.message }}</div>
          <div class="alert-suggestion">💡 {{ alert.suggestion }}</div>
        </div>
      </div>
    </div>

    <!-- 舆情历史 -->
    <div class="card">
      <h3>📜 舆情历史</h3>
      <div class="history-list" v-if="sentimentHistory.length > 0">
        <div v-for="(record, idx) in sentimentHistory" :key="idx" class="history-item">
          <span class="history-time">{{ formatTime(record.timestamp) }}</span>
          <span class="history-fg" :class="getFgClass(record.fear_greed)">
            {{ record.fear_greed?.toFixed(1) }}
          </span>
          <span class="history-state">{{ record.market_state }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const fearGreed = ref<any>(null)
const sentimentIndex = ref<any>(null)
const newsList = ref<any[]>([])
const sentimentAlerts = ref<any[]>([])
const sentimentHistory = ref<any[]>([])
const selectedSymbol = ref('BTCUSDT')

const apiBase = '/api'

const totalNews = computed(() => {
  if (!sentimentIndex.value?.sentiment_distribution) return 1
  const d = sentimentIndex.value.sentiment_distribution
  return (d.positive || 0) + (d.neutral || 0) + (d.negative || 0) || 1
})

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString('zh-CN')
}

const sentimentLabelText = (label: string) => {
  const map: Record<string, string> = {
    positive: '😊 正面',
    negative: '😟 负面',
    neutral: '😐 中性'
  }
  return map[label] || label
}

const getFgClass = (value: number) => {
  if (value < 25) return 'extreme_fear'
  if (value < 45) return 'fear'
  if (value < 55) return 'neutral'
  if (value < 75) return 'greed'
  return 'extreme_greed'
}

const fetchFearGreed = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-sentiment/fear-greed?symbol=${selectedSymbol.value}`)
    fearGreed.value = await response.json()
  } catch (error) {
    console.error('获取恐惧贪婪指数失败:', error)
  }
}

const fetchSentimentIndex = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-sentiment/index/${selectedSymbol.value}?news_count=20`)
    sentimentIndex.value = await response.json()
  } catch (error) {
    console.error('获取舆情指数失败:', error)
  }
}

const fetchNews = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-sentiment/news/${selectedSymbol.value}?count=20`)
    const data = await response.json()
    newsList.value = data.news || []
  } catch (error) {
    console.error('获取新闻失败:', error)
  }
}

const fetchAlerts = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-sentiment/alerts/${selectedSymbol.value}`)
    const data = await response.json()
    sentimentAlerts.value = data.alerts || []
  } catch (error) {
    console.error('获取舆情预警失败:', error)
  }
}

const fetchHistory = async () => {
  try {
    const response = await fetch(`${apiBase}/enhanced-sentiment/history/${selectedSymbol.value}?limit=50`)
    const data = await response.json()
    sentimentHistory.value = data.history || []
  } catch (error) {
    console.error('获取舆情历史失败:', error)
  }
}

const refreshAll = async () => {
  await Promise.all([
    fetchFearGreed(),
    fetchSentimentIndex(),
    fetchNews(),
    fetchAlerts(),
    fetchHistory()
  ])
}

onMounted(() => {
  refreshAll()
  setInterval(refreshAll, 60000) // 每分钟刷新
})
</script>

<style scoped>
.enhanced-sentiment {
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

.fear-greed-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.fear-greed-card h3 {
  color: white;
}

.fear-greed-main {
  padding: 16px 0;
}

.fear-greed-meter {
  margin-bottom: 24px;
}

.meter-scale {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  opacity: 0.9;
}

.meter-bar {
  position: relative;
  height: 20px;
  background: rgba(255,255,255,0.2);
  border-radius: 10px;
  overflow: visible;
}

.meter-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.5s;
}

.meter-fill.极度恐惧,
.meter-fill.恐惧 {
  background: linear-gradient(90deg, #ef4444, #f97316);
}

.meter-fill.中性 {
  background: linear-gradient(90deg, #f97316, #eab308);
}

.meter-fill.贪婪,
.meter-fill.极度贪婪 {
  background: linear-gradient(90deg, #eab308, #22c55e);
}

.meter-pointer {
  position: absolute;
  top: -8px;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 12px solid white;
  transform: translateX(-50%);
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.fear-greed-value {
  text-align: center;
}

.value-number {
  font-size: 56px;
  font-weight: bold;
}

.value-emoji {
  font-size: 32px;
  margin: 0 12px;
}

.value-label {
  font-size: 20px;
  opacity: 0.95;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.overview-item {
  text-align: center;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.overview-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.overview-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.overview-value.positive {
  color: #10b981;
}

.overview-value.negative {
  color: #ef4444;
}

.sentiment-distribution h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dist-item {
  display: grid;
  grid-template-columns: 60px 1fr 50px;
  gap: 12px;
  align-items: center;
}

.dist-label {
  color: #666;
}

.dist-bar {
  height: 24px;
  background: #f5f5f5;
  border-radius: 12px;
  overflow: hidden;
}

.dist-fill {
  height: 100%;
  transition: width 0.3s;
}

.dist-fill.positive {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.dist-fill.neutral {
  background: linear-gradient(90deg, #6b7280, #9ca3af);
}

.dist-fill.negative {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.dist-count {
  text-align: right;
  color: #666;
  font-weight: 600;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.sentiment-tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.sentiment-tag.positive {
  background: #d1fae5;
  color: #065f46;
}

.sentiment-tag.negative {
  background: #fee2e2;
  color: #7f1d1d;
}

.sentiment-tag.neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.sentiment-score {
  font-size: 12px;
  color: #666;
}

.news-topics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.topic-tag {
  padding: 4px 10px;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 8px;
  font-size: 11px;
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: grid;
  grid-template-columns: 180px 80px 1fr;
  gap: 12px;
  padding: 12px;
  background: #f8f9ff;
  border-radius: 8px;
  align-items: center;
}

.history-time {
  color: #666;
  font-size: 13px;
}

.history-fg {
  font-weight: 600;
}

.history-fg.extreme_fear,
.history-fg.fear {
  color: #ef4444;
}

.history-fg.extreme_greed,
.history-fg.greed {
  color: #10b981;
}

.history-fg.neutral {
  color: #6b7280;
}

.history-state {
  color: #666;
}

@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .history-item {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
}
</style>

