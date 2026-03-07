<template>
  <div class="realtime-sentiment-container">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📊 实时舆情监控</span>
          <el-tag type="primary">舆情分析</el-tag>
        </div>
      </template>
      
      <div class="control-panel">
        <el-input
          v-model="keyword"
          placeholder="输入关键词（如：BTC, ETH, RIVER）"
          clearable
          @keyup.enter="monitorKeyword"
        >
          <template #append>
            <el-button @click="monitorKeyword">监控</el-button>
          </template>
        </el-input>
      </div>
      
      <el-tabs v-model="activeTab" class="content-tabs">
        <el-tab-pane label="实时状态" name="status">
          <div v-if="sentimentStatus" class="status-panel">
            <div class="status-header">
              <h3>{{ sentimentStatus.keyword }}</h3>
              <el-tag :type="getStatusType(sentimentStatus.status)">
                {{ sentimentStatus.status === 'active' ? '🟢 活跃' : '🟡 无数据' }}
              </el-tag>
            </div>
            
            <div v-if="sentimentStatus.status === 'active'" class="status-content">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="最新分数">
                  <el-progress
                    :percentage="sentimentStatus.latest_data.overall_score?.score || 50"
                    :color="getScoreColor(sentimentStatus.latest_data.overall_score?.score || 50)"
                  />
                </el-descriptions-item>
                <el-descriptions-item label="趋势">
                  {{ sentimentStatus.trend?.label || '➡️ 稳定' }}
                </el-descriptions-item>
                <el-descriptions-item label="数据点">
                  {{ sentimentStatus.data_points }}
                </el-descriptions-item>
                <el-descriptions-item label="预警数">
                  {{ sentimentStatus.recent_alerts?.length || 0 }}
                </el-descriptions-item>
              </el-descriptions>
              
              <div v-if="sentimentStatus.recent_alerts?.length > 0" class="alerts-section">
                <h4>⚠️ 最近预警</h4>
                <el-timeline>
                  <el-timeline-item
                    v-for="alert in sentimentStatus.recent_alerts"
                    :key="alert.id"
                    :type="getAlertType(alert.level)"
                  >
                    <strong>{{ alert.title }}</strong>
                    <p>{{ alert.message }}</p>
                    <small>{{ alert.datetime }}</small>
                  </el-timeline-item>
                </el-timeline>
              </div>
            </div>
          </div>
          <el-empty v-else description="请先输入关键词并点击监控" />
        </el-tab-pane>
        
        <el-tab-pane label="历史数据可视化" name="visualization">
          <div class="visualization-panel">
            <div class="chart-placeholder">
              <el-empty description="图表组件待集成ECharts">
                <template #image>
                  <div class="chart-info">
                    <p>📈 舆情分数时间序列</p>
                    <p>📰 新闻情感趋势</p>
                    <p>💬 社交情感趋势</p>
                  </div>
                  <p>可从 API 获取数据：<code>/api/realtime-sentiment/visualization/{keyword}</code></p>
                </template>
              </el-empty>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="历史记录" name="history">
          <div class="history-panel">
            <el-table :data="sentimentHistory" stripe>
              <el-table-column prop="datetime" label="时间" width="180" />
              <el-table-column prop="keyword" label="关键词" width="120" />
              <el-table-column label="分数" width="120">
                <template #default="{ row }">
                  <el-tag :type="getScoreTagType(row.data?.overall_score?.score)">
                    {{ row.data?.overall_score?.score?.toFixed(1) || 'N/A' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="新闻情感" width="120">
                <template #default="{ row }">
                  {{ row.data?.news_sentiment?.sentiment_score?.toFixed(2) || 'N/A' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="舆情摘要" name="summary">
          <div v-if="sentimentSummary" class="summary-panel">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="统计周期">
                {{ sentimentSummary.period?.start }} ~ {{ sentimentSummary.period?.end }}
              </el-descriptions-item>
              <el-descriptions-item label="数据量">
                {{ sentimentSummary.period?.count }}
              </el-descriptions-item>
              <el-descriptions-item label="平均分数">
                {{ sentimentSummary.overall_score?.mean?.toFixed(1) }}
              </el-descriptions-item>
              <el-descriptions-item label="预警次数">
                {{ sentimentSummary.alert_count }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="暂无摘要数据" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const keyword = ref('crypto')
const activeTab = ref('status')
const sentimentStatus = ref<any>(null)
const sentimentHistory = ref<any[]>([])
const sentimentSummary = ref<any>(null)

const monitorKeyword = async () => {
  try {
    ElMessage.info(`正在监控 ${keyword.value}...`)
    // TODO: 调用 API
    // const response = await fetch(`/api/realtime-sentiment/monitor/${keyword.value}`)
    // const data = await response.json()
    ElMessage.success('监控成功！')
  } catch (error) {
    ElMessage.error('监控失败')
  }
}

const getStatusType = (status: string) => {
  return status === 'active' ? 'success' : 'warning'
}

const getScoreColor = (score: number) => {
  if (score >= 70) return '#67C23A'
  if (score >= 50) return '#E6A23C'
  return '#F56C6C'
}

const getScoreTagType = (score: number) => {
  if (!score) return 'info'
  if (score >= 70) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

const getAlertType = (level: string) => {
  if (level === 'warning') return 'warning'
  if (level === 'danger') return 'danger'
  return 'info'
}
</script>

<style scoped>
.realtime-sentiment-container {
  padding: 20px;
}

.main-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-panel {
  margin-bottom: 20px;
}

.content-tabs {
  margin-top: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status-header h3 {
  margin: 0;
}

.alerts-section {
  margin-top: 20px;
}

.alerts-section h4 {
  margin-bottom: 10px;
}

.chart-placeholder {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-info {
  text-align: left;
  margin-bottom: 20px;
}
</style>
