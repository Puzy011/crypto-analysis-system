<template>
  <div class="sentiment">
    <el-row :gutter="20">
      <!-- 左侧：设置 -->
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📰 舆情分析设置</span>
            </div>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="关键词">
              <el-select v-model="keyword" @change="loadSentiment">
                <el-option label="BTC" value="BTC" />
                <el-option label="ETH" value="ETH" />
                <el-option label="XRP" value="XRP" />
                <el-option label="Crypto" value="crypto" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="loadSentiment" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 恐慌贪婪指数 -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>😨 恐慌贪婪指数</span>
            </div>
          </template>
          
          <div v-if="fearGreedIndex" class="fear-greed">
            <div class="score-display">
              <div class="score-value" :style="{ color: getFearGreedColor(fearGreedIndex.color) }">
                {{ fearGreedIndex.score.toFixed(0) }}
              </div>
              <div class="score-label">{{ fearGreedIndex.label }}</div>
            </div>
            <el-progress 
              :percentage="fearGreedIndex.score" 
              :color="getFearGreedColors()"
              :stroke-width="20"
            />
          </div>
          <div v-else class="loading">
            <el-skeleton :rows="3" animated />
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：分析结果 -->
      <el-col :span="18">
        <!-- 新闻舆情 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>📰 新闻舆情</span>
              <el-tag v-if="newsSentiment" :type="getSentimentTagType(newsSentiment.overall_sentiment)">
                {{ newsSentiment.sentiment_label }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="!newsSentiment" class="loading">
            <el-skeleton :rows="5" animated />
          </div>
          
          <div v-else class="news-result">
            <div class="sentiment-score">
              <div class="label">舆情分数</div>
              <div class="score-value" :class="getScoreClass(newsSentiment.sentiment_score)">
                {{ newsSentiment.sentiment_score >= 0 ? '+' : '' }}{{ (newsSentiment.sentiment_score * 100).toFixed(0) }}
              </div>
            </div>
            
            <el-divider />
            
            <div class="breakdown">
              <div class="breakdown-item positive">
                <span class="label">正面新闻</span>
                <el-tag type="success">{{ newsSentiment.breakdown.positive }}</el-tag>
              </div>
              <div class="breakdown-item neutral">
                <span class="label">中性新闻</span>
                <el-tag type="info">{{ newsSentiment.breakdown.neutral }}</el-tag>
              </div>
              <div class="breakdown-item negative">
                <span class="label">负面新闻</span>
                <el-tag type="danger">{{ newsSentiment.breakdown.negative }}</el-tag>
              </div>
            </div>
            
            <el-divider />
            
            <div class="recent-news">
              <div class="title">📰 最近新闻</div>
              <el-list>
                <el-list-item 
                  v-for="(news, index) in newsSentiment.recent_news" 
                  :key="index"
                >
                  <div class="news-item">
                    <el-tag 
                      size="small"
                      :type="getNewsTagType(news.sentiment)"
                      style="margin-right: 10px;"
                    >
                      {{ getNewsSentimentLabel(news.sentiment) }}
                    </el-tag>
                    <span class="news-title">{{ news.title }}</span>
                  </div>
                </el-list-item>
              </el-list>
            </div>
          </div>
        </el-card>
        
        <!-- 社交媒体舆情 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🐦 社交媒体舆情</span>
            </div>
          </template>
          
          <div v-if="!socialSentiment" class="loading">
            <el-skeleton :rows="5" animated />
          </div>
          
          <div v-else class="social-result">
            <div class="hot-topics">
              <div class="title">🔥 热门话题</div>
              <div class="tags">
                <el-tag 
                  v-for="(topic, index) in socialSentiment.hot_topics" 
                  :key="index"
                  style="margin-right: 8px; margin-bottom: 8px;"
                >
                  {{ topic }}
                </el-tag>
              </div>
            </div>
            
            <el-divider />
            
            <div class="heatmap">
              <div class="title">📊 情绪热力图</div>
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-card shadow="hover" size="small">
                    <div class="hm-label">恐慌贪婪</div>
                    <div class="hm-value" :class="getHeatmapClass(socialSentiment.heatmap.fear_greed)">
                      {{ socialSentiment.heatmap.fear_greed.toFixed(0) }}
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card shadow="hover" size="small">
                    <div class="hm-label">Twitter</div>
                    <div class="hm-value" :class="getHeatmapClass(socialSentiment.heatmap.twitter_sentiment * 50 + 50)">
                      {{ (socialSentiment.heatmap.twitter_sentiment * 100).toFixed(0) }}
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card shadow="hover" size="small">
                    <div class="hm-label">Reddit</div>
                    <div class="hm-value" :class="getHeatmapClass(socialSentiment.heatmap.reddit_sentiment * 50 + 50)">
                      {{ (socialSentiment.heatmap.reddit_sentiment * 100).toFixed(0) }}
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card shadow="hover" size="small">
                    <div class="hm-label">Telegram</div>
                    <div class="hm-value" :class="getHeatmapClass(socialSentiment.heatmap.telegram_sentiment * 50 + 50)">
                      {{ (socialSentiment.heatmap.telegram_sentiment * 100).toFixed(0) }}
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const keyword = ref('crypto')
const loading = ref(false)
const newsSentiment = ref<any>(null)
const socialSentiment = ref<any>(null)
const fearGreedIndex = ref<any>(null)

const loadSentiment = async () => {
  loading.value = true
  
  try {
    // 加载新闻舆情
    const newsResponse = await axios.get(`/api/sentiment/news/${keyword.value}`)
    if (newsResponse.data.success) {
      newsSentiment.value = newsResponse.data.data
    }
    
    // 加载社交媒体舆情
    const socialResponse = await axios.get(`/api/sentiment/social/${keyword.value}`)
    if (socialResponse.data.success) {
      socialSentiment.value = socialResponse.data.data
    }
    
    // 加载恐慌贪婪指数
    const fgResponse = await axios.get('/api/sentiment/fear-greed')
    if (fgResponse.data.success) {
      fearGreedIndex.value = fgResponse.data.data
    }
  } catch (error) {
    console.error('加载舆情分析失败:', error)
    ElMessage.error('加载舆情分析失败')
  } finally {
    loading.value = false
  }
}

const getSentimentTagType = (sentiment: string): string => {
  const types: Record<string, string> = {
    bullish: 'success',
    bearish: 'danger',
    neutral: 'info'
  }
  return types[sentiment] || ''
}

const getNewsTagType = (sentiment: string): string => {
  const types: Record<string, string> = {
    positive: 'success',
    negative: 'danger',
    neutral: 'info'
  }
  return types[sentiment] || ''
}

const getNewsSentimentLabel = (sentiment: string): string => {
  const labels: Record<string, string> = {
    positive: '正面',
    negative: '负面',
    neutral: '中性'
  }
  return labels[sentiment] || sentiment
}

const getScoreClass = (score: number): string => {
  if (score > 0) return 'positive'
  if (score < 0) return 'negative'
  return ''
}

const getFearGreedColor = (color: string): string => {
  const colors: Record<string, string> = {
    success: '#67c23a',
    warning: '#e6a23c',
    danger: '#f56c6c',
    info: '#909399'
  }
  return colors[color] || '#909399'
}

const getFearGreedColors = () => {
  return [
    { color: '#f56c6c', percentage: 20 },
    { color: '#e6a23c', percentage: 45 },
    { color: '#909399', percentage: 55 },
    { color: '#e6a23c', percentage: 75 },
    { color: '#67c23a', percentage: 100 }
  ]
}

const getHeatmapClass = (value: number): string => {
  if (value > 70) return 'positive'
  if (value < 30) return 'negative'
  return ''
}

onMounted(() => {
  loadSentiment()
})
</script>

<style scoped>
.sentiment {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading {
  padding: 20px 0;
}

.fear-greed {
  text-align: center;
  padding: 10px 0;
}

.score-display {
  margin-bottom: 20px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 10px;
}

.score-label {
  font-size: 18px;
  color: #606266;
}

.news-result {
  padding: 10px 0;
}

.sentiment-score {
  text-align: center;
  margin-bottom: 20px;
}

.sentiment-score .label {
  display: block;
  color: #606266;
  margin-bottom: 8px;
}

.sentiment-score .score-value {
  font-size: 36px;
  font-weight: 700;
}

.sentiment-score .score-value.positive {
  color: #67c23a;
}

.sentiment-score .score-value.negative {
  color: #f56c6c;
}

.breakdown {
  display: flex;
  justify-content: space-around;
  gap: 20px;
  margin-bottom: 20px;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.breakdown-item .label {
  color: #909399;
  font-size: 13px;
}

.recent-news {
  margin-top: 10px;
}

.recent-news .title {
  color: #606266;
  margin-bottom: 15px;
  font-weight: 600;
}

.news-item {
  display: flex;
  align-items: center;
}

.news-title {
  flex: 1;
  color: #303133;
}

.social-result {
  padding: 10px 0;
}

.hot-topics {
  margin-bottom: 20px;
}

.hot-topics .title {
  color: #606266;
  margin-bottom: 15px;
  font-weight: 600;
}

.tags {
  display: flex;
  flex-wrap: wrap;
}

.heatmap {
  margin-top: 10px;
}

.heatmap .title {
  color: #606266;
  margin-bottom: 15px;
  font-weight: 600;
}

.hm-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
  text-align: center;
}

.hm-value {
  font-size: 24px;
  font-weight: 700;
  text-align: center;
}

.hm-value.positive {
  color: #67c23a;
}

.hm-value.negative {
  color: #f56c6c;
}
</style>
