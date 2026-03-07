<template>
  <div class="realtime-prediction-container">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>🔮 实时预测更新</span>
          <el-tag type="primary">预测系统</el-tag>
        </div>
      </template>
      
      <div class="control-panel">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-input
              v-model="symbol"
              placeholder="输入交易对（如：BTCUSDT, RIVERUSDT）"
              clearable
            />
          </el-col>
          <el-col :span="6">
            <el-button type="primary" @click="getLatestPrediction">
              获取最新预测
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button @click="getSummary">
              查看摘要
            </el-button>
          </el-col>
        </el-row>
      </div>
      
      <el-tabs v-model="activeTab" class="content-tabs">
        <el-tab-pane label="最新预测" name="latest">
          <div v-if="latestPrediction" class="latest-panel">
            <div class="prediction-card">
              <div class="prediction-header">
                <h3>{{ latestPrediction.symbol }}</h3>
                <el-tag :type="getDirectionType(latestPrediction.prediction?.direction)" size="large">
                  {{ getDirectionLabel(latestPrediction.prediction?.direction) }}
                </el-tag>
              </div>
              
              <el-descriptions :column="2" border class="prediction-details">
                <el-descriptions-item label="置信度">
                  <el-progress
                    :percentage="latestPrediction.prediction?.confidence || 0"
                    :color="getConfidenceColor(latestPrediction.prediction?.confidence || 0)"
                  />
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ latestPrediction.datetime }}
                </el-descriptions-item>
                <el-descriptions-item label="预测价格">
                  {{ latestPrediction.prediction?.predicted_price ? '$' + latestPrediction.prediction.predicted_price.toFixed(4) : 'N/A' }}
                </el-descriptions-item>
                <el-descriptions-item label="来源">
                  <el-tag>{{ latestPrediction.source }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="版本" :span="2">
                  v{{ latestPrediction.version }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <el-empty v-else description="请先获取最新预测" />
        </el-tab-pane>
        
        <el-tab-pane label="预测变化分析" name="changes">
          <div v-if="predictionChanges" class="changes-panel">
            <div class="changes-header">
              <h3>{{ predictionChanges.symbol }}</h3>
              <el-tag :type="getChangeLevelType(predictionChanges.change_level)" size="large">
                {{ predictionChanges.change_label }}
              </el-tag>
            </div>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-card class="change-card">
                  <template #header>
                    <span>方向变化</span>
                  </template>
                  <div v-if="predictionChanges.direction_change?.changed" class="direction-change">
                    <p>
                      从 <el-tag :type="getDirectionType(predictionChanges.direction_change.from)">
                        {{ getDirectionLabel(predictionChanges.direction_change.from) }}
                      </el-tag>
                    </p>
                    <p>
                      到 <el-tag :type="getDirectionType(predictionChanges.direction_change.to)">
                        {{ getDirectionLabel(predictionChanges.direction_change.to) }}
                      </el-tag>
                    </p>
                  </div>
                  <div v-else>
                    <p>方向保持不变：</p>
                    <el-tag :type="getDirectionType(predictionChanges.direction_change?.current)">
                      {{ getDirectionLabel(predictionChanges.direction_change?.current) }}
                    </el-tag>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="change-card">
                  <template #header>
                    <span>置信度变化</span>
                  </template>
                  <div class="confidence-change">
                    <p>
                      之前: <el-tag>{{ predictionChanges.confidence_change?.previous?.toFixed(1) }}%</el-tag>
                    </p>
                    <p>
                      现在: <el-tag :type="getConfidenceTagType(predictionChanges.confidence_change?.current)">
                        {{ predictionChanges.confidence_change?.current?.toFixed(1) }}%
                      </el-tag>
                    </p>
                    <p>
                      变化: 
                      <span :class="{ 'positive': predictionChanges.confidence_change?.delta > 0, 'negative': predictionChanges.confidence_change?.delta < 0 }">
                        {{ predictionChanges.confidence_change?.delta > 0 ? '+' : '' }}{{ predictionChanges.confidence_change?.delta?.toFixed(1) }}%
                      </span>
                    </p>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <div v-if="predictionChanges.price_change" class="price-change-section">
              <h4>💰 价格预测变化</h4>
              <el-descriptions :column="3" border>
                <el-descriptions-item label="之前价格">
                  {{ predictionChanges.price_change.previous ? '$' + predictionChanges.price_change.previous.toFixed(4) : 'N/A' }}
                </el-descriptions-item>
                <el-descriptions-item label="当前价格">
                  {{ predictionChanges.price_change.current ? '$' + predictionChanges.price_change.current.toFixed(4) : 'N/A' }}
                </el-descriptions-item>
                <el-descriptions-item label="变化幅度">
                  <span :class="{ 'positive': predictionChanges.price_change.change_pct > 0, 'negative': predictionChanges.price_change.change_pct < 0 }">
                    {{ predictionChanges.price_change.change_pct ? (predictionChanges.price_change.change_pct * 100).toFixed(2) + '%' : 'N/A' }}
                  </span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <el-empty v-else description="请先分析预测变化" />
        </el-tab-pane>
        
        <el-tab-pane label="预测历史" name="history">
          <div class="history-panel">
            <el-table :data="predictionHistory" stripe>
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="datetime" label="时间" width="180" />
              <el-table-column prop="symbol" label="交易对" width="120" />
              <el-table-column label="预测方向" width="120">
                <template #default="{ row }">
                  <el-tag :type="getDirectionType(row.prediction?.direction)">
                    {{ getDirectionLabel(row.prediction?.direction) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="置信度" width="100">
                <template #default="{ row }">
                  {{ row.prediction?.confidence?.toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column label="预测价格" width="140">
                <template #default="{ row }">
                  {{ row.prediction?.predicted_price ? '$' + row.prediction.predicted_price.toFixed(4) : 'N/A' }}
                </template>
              </el-table-column>
              <el-table-column label="来源" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.source }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="更新预测" name="update">
          <div class="update-panel">
            <el-form :model="updateForm" label-width="120px">
              <el-form-item label="交易对">
                <el-input v-model="updateForm.symbol" placeholder="如：BTCUSDT" />
              </el-form-item>
              <el-form-item label="预测方向">
                <el-select v-model="updateForm.prediction.direction" placeholder="选择方向">
                  <el-option label="看涨 📈" value="up" />
                  <el-option label="看跌 📉" value="down" />
                  <el-option label="震荡 ➡️" value="sideways" />
                </el-select>
              </el-form-item>
              <el-form-item label="置信度">
                <el-slider
                  v-model="updateForm.prediction.confidence"
                  :min="0"
                  :max="100"
                  :show-input
                />
              </el-form-item>
              <el-form-item label="预测价格（可选）">
                <el-input-number v-model="updateForm.prediction.predicted_price" :min="0" :step="0.0001" />
              </el-form-item>
              <el-form-item label="来源">
                <el-select v-model="updateForm.source" placeholder="选择来源">
                  <el-option label="手动" value="manual" />
                  <el-option label="自动" value="auto" />
                  <el-option label="AI模型" value="ai_model" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="updatePrediction">
                  更新预测
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="系统摘要" name="summary">
          <div v-if="systemSummary" class="summary-panel">
            <el-card>
              <template #header>
                <span>📊 系统概览</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="监控的交易对数量">
                  <el-statistic :value="systemSummary.total_symbols || 0" />
                </el-descriptions-item>
                <el-descriptions-item label="交易对列表">
                  <el-tag v-for="sym in systemSummary.symbols" :key="sym" style="margin-right: 5px; margin-bottom: 5px;">
                    {{ sym }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="生成时间">
                  {{ systemSummary.generated_datetime }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
            
            <div v-if="systemSummary.latest_predictions" class="latest-predictions-section">
              <h4>🔄 各交易对最新预测</h4>
              <el-row :gutter="20">
                <el-col
                  v-for="(pred, sym) in systemSummary.latest_predictions"
                  :key="sym"
                  :span="8"
                >
                  <el-card shadow="hover" class="prediction-mini-card">
                    <div class="mini-card-header">
                      <strong>{{ sym }}</strong>
                      <el-tag :type="getDirectionType(pred.prediction?.direction)" size="small">
                        {{ getDirectionLabel(pred.prediction?.direction) }}
                      </el-tag>
                    </div>
                    <p>置信度: {{ pred.prediction?.confidence?.toFixed(1) }}%</p>
                    <p class="mini-time">{{ pred.datetime }}</p>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </div>
          <el-empty v-else description="请先查看系统摘要" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const symbol = ref('BTCUSDT')
const activeTab = ref('latest')
const latestPrediction = ref<any>(null)
const predictionChanges = ref<any>(null)
const predictionHistory = ref<any[]>([])
const systemSummary = ref<any>(null)

const updateForm = reactive({
  symbol: '',
  prediction: {
    direction: '',
    confidence: 50,
    predicted_price: null
  },
  source: 'manual'
})

const getLatestPrediction = async () => {
  try {
    ElMessage.info(`正在获取 ${symbol.value} 的最新预测...`)
    // TODO: 调用 API
    // const response = await fetch(`/api/realtime-prediction/latest/${symbol.value}`)
    // const data = await response.json()
    // latestPrediction.value = data.data
    ElMessage.success('获取成功！')
  } catch (error) {
    ElMessage.error('获取失败')
  }
}

const getSummary = async () => {
  try {
    ElMessage.info('正在获取系统摘要...')
    // TODO: 调用 API
    // const response = await fetch(`/api/realtime-prediction/summary?symbol=${symbol.value}`)
    // const data = await response.json()
    // systemSummary.value = data.data
    ElMessage.success('获取成功！')
  } catch (error) {
    ElMessage.error('获取失败')
  }
}

const updatePrediction = async () => {
  try {
    ElMessage.info('正在更新预测...')
    // TODO: 调用 API
    // const response = await fetch('/api/realtime-prediction/update', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(updateForm)
    // })
    ElMessage.success('预测已更新！')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const getDirectionType = (direction: string) => {
  if (direction === 'up') return 'success'
  if (direction === 'down') return 'danger'
  return 'info'
}

const getDirectionLabel = (direction: string) => {
  if (direction === 'up') return '📈 看涨'
  if (direction === 'down') return '📉 看跌'
  if (direction === 'sideways') return '➡️ 震荡'
  return direction
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 80) return '#67C23A'
  if (confidence >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getConfidenceTagType = (confidence: number) => {
  if (!confidence) return 'info'
  if (confidence >= 80) return 'success'
  if (confidence >= 60) return 'warning'
  return 'danger'
}

const getChangeLevelType = (level: string) => {
  if (level === 'major') return 'danger'
  if (level === 'significant') return 'warning'
  if (level === 'moderate') return 'primary'
  return 'info'
}
</script>

<style scoped>
.realtime-prediction-container {
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

.prediction-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  color: white;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.prediction-header h3 {
  margin: 0;
  font-size: 24px;
}

.prediction-details :deep(.el-descriptions__label),
.prediction-details :deep(.el-descriptions__content) {
  color: white !important;
}

.changes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.changes-header h3 {
  margin: 0;
}

.change-card {
  margin-bottom: 20px;
}

.direction-change p,
.confidence-change p {
  margin: 10px 0;
}

.positive {
  color: #67C23A;
  font-weight: bold;
}

.negative {
  color: #F56C6C;
  font-weight: bold;
}

.price-change-section {
  margin-top: 30px;
}

.price-change-section h4 {
  margin-bottom: 15px;
}

.update-panel {
  max-width: 600px;
  margin: 0 auto;
}

.latest-predictions-section {
  margin-top: 30px;
}

.latest-predictions-section h4 {
  margin-bottom: 15px;
}

.prediction-mini-card {
  margin-bottom: 15px;
}

.mini-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.mini-time {
  color: #909399;
  font-size: 12px;
  margin: 0;
}
</style>
