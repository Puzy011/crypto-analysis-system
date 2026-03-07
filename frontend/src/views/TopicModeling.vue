<template>
  <div class="topic-modeling">
    <div class="page-header">
      <h1>🧠 主题建模</h1>
      <p>LDA 风格主题建模 + 事件类型识别</p>
    </div>

    <!-- 刷新按钮 -->
    <div class="refresh-section">
      <button @click="refreshAll" class="btn btn-primary" :disabled="isLoading">
        {{ isLoading ? '⏳ 分析中...' : '🔄 分析新闻主题' }}
      </button>
    </div>

    <!-- 主题建模结果 -->
    <div class="card topics-card" v-if="topicAnalysis">
      <h3>📊 LDA 风格主题建模</h3>
      
      <div class="topics-summary">
        <div class="summary-item">
          <span class="summary-label">分析文档数</span>
          <span class="summary-value">{{ topicAnalysis.lda_topic_modeling?.num_documents }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">识别主题数</span>
          <span class="summary-value">{{ topicAnalysis.lda_topic_modeling?.num_topics }}</span>
        </div>
      </div>

      <div class="topics-list" v-if="topicAnalysis.lda_topic_modeling?.topics?.length > 0">
        <div 
          v-for="topic in topicAnalysis.lda_topic_modeling.topics" 
          :key="topic.topic_id"
          class="topic-item"
        >
          <div class="topic-header">
            <span class="topic-name">{{ topic.topic_name }}</span>
            <span class="topic-proportion">{{ (topic.proportion * 100).toFixed(1) }}%</span>
          </div>
          <div class="topic-words">
            <span 
              v-for="(word, idx) in topic.top_words" 
              :key="idx"
              class="topic-word"
            >
              {{ word }}
            </span>
          </div>
        </div>
      </div>

      <div class="topic-distribution" v-if="topicAnalysis.lda_topic_modeling?.topic_distribution">
        <h4>📈 主题分布</h4>
        <div class="distribution-list">
          <div 
            v-for="(proportion, topic) in topicAnalysis.lda_topic_modeling.topic_distribution" 
            :key="topic"
            class="distribution-item"
          >
            <span class="dist-topic">{{ getTopicName(topic) }}</span>
            <div class="dist-bar">
              <div 
                class="dist-fill" 
                :style="{ width: (proportion * 100) + '%' }"
              ></div>
            </div>
            <span class="dist-value">{{ (proportion * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 关键主题 -->
    <div class="card themes-card" v-if="topicAnalysis?.key_themes">
      <h3>🎯 关键主题</h3>
      <div class="themes-list">
        <div 
          v-for="(theme, idx) in topicAnalysis.key_themes" 
          :key="idx"
          class="theme-item"
        >
          <div class="theme-header">
            <span class="theme-name">{{ theme.theme }}</span>
            <span class="theme-score" v-if="theme.score > 0">
              分数: {{ theme.score }}
            </span>
          </div>
          <div class="theme-words" v-if="theme.matched_words?.length > 0">
            <span 
              v-for="(word, i) in theme.matched_words" 
              :key="i"
              class="theme-word"
            >
              {{ word }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新闻事件分析 -->
    <div class="card events-card" v-if="topicAnalysis?.news_with_events">
      <h3>📰 新闻事件分析</h3>
      <div class="events-list">
        <div 
          v-for="news in topicAnalysis.news_with_events?.slice(0, 10)" 
          :key="news.id"
          class="event-news-item"
        >
          <div class="news-header">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ formatTime(news.timestamp) }}</span>
          </div>
          <div class="news-title">{{ news.title }}</div>
          
          <div class="news-events" v-if="news.event_analysis?.detected_events?.length > 0">
            <div 
              v-for="(event, idx) in news.event_analysis.detected_events" 
              :key="idx"
              class="event-tag"
            >
              {{ event.event_name }}
              <span class="matched-keyword">({{ event.matched_keyword }})</span>
            </div>
          </div>
          <div 
            v-else 
            class="no-events"
          >
            未检测到特定事件类型
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isLoading = ref(false)
const topicAnalysis = ref<any>(null)

const apiBase = '/api'

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString('zh-CN')
}

const getTopicName = (topicId: string) => {
  const names: Record<string, string> = {
    'regulation': '监管政策',
    'adoption': '机构采用',
    'technology': '技术发展',
    'market': '市场动态',
    'exchange': '交易所',
    'security': '安全事件',
    'defi': 'DeFi 生态',
    'nft': 'NFT/元宇宙',
    'other': '其他'
  }
  return names[topicId] || topicId
}

const refreshAll = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${apiBase}/topic-modeling/from-news/BTCUSDT?news_count=20`)
    topicAnalysis.value = await response.json()
  } catch (error) {
    console.error('获取主题分析失败:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.topic-modeling {
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
  margin: 20px 0 12px 0;
  color: #333;
  font-size: 15px;
}

.topics-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
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
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-item {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.topic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.topic-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.topic-proportion {
  font-size: 14px;
  color: #667eea;
  font-weight: 600;
}

.topic-words {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-word {
  padding: 6px 14px;
  background: white;
  border-radius: 12px;
  font-size: 13px;
  color: #333;
}

.topic-distribution {
  margin-top: 20px;
}

.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.distribution-item {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  gap: 12px;
  align-items: center;
}

.dist-topic {
  font-weight: 500;
  color: #333;
}

.dist-bar {
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  overflow: hidden;
}

.dist-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.dist-value {
  text-align: right;
  font-weight: 600;
  color: #333;
}

.themes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-item {
  padding: 16px;
  background: #f8f9ff;
  border-radius: 12px;
}

.theme-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.theme-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.theme-score {
  font-size: 13px;
  color: #667eea;
}

.theme-words {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.theme-word {
  padding: 4px 10px;
  background: white;
  border-radius: 12px;
  font-size: 12px;
  color: #333;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-news-item {
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

.news-events {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.event-tag {
  padding: 6px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.matched-keyword {
  opacity: 0.9;
  font-weight: 400;
  margin-left: 4px;
}

.no-events {
  color: #999;
  font-size: 13px;
  font-style: italic;
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

@media (max-width: 768px) {
  .distribution-item {
    grid-template-columns: 100px 1fr 60px;
  }
}
</style>

