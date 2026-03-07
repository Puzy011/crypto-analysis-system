<template>
  <div class="prediction-backtest-container">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📊 预测回测验证</span>
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
            <el-button type="primary" @click="runMockBacktest">
              运行模拟回测
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button @click="getReport">
              查看回测报告
            </el-button>
          </el-col>
        </el-row>
      </div>
      
      <el-tabs v-model="activeTab" class="content-tabs">
        <el-tab-pane label="回测报告" name="report">
          <div v-if="backtestReport" class="report-panel">
            <div class="report-header">
              <h3>{{ backtestReport.symbol }}</h3>
              <el-tag :type="getGradeType(backtestReport.grade)" size="large">
                {{ backtestReport.label }}
              </el-tag>
            </div>
            
            <el-descriptions :column="2" border class="report-stats">
              <el-descriptions-item label="总验证数">
                <el-statistic :value="backtestReport.accuracy_stats?.total_verified || 0" />
              </el-descriptions-item>
              <el-descriptions-item label="正确预测">
                <el-statistic :value="backtestReport.accuracy_stats?.correct_predictions || 0" />
              </el-descriptions-item>
              <el-descriptions-item label="准确率">
                <el-progress
                  :percentage="(backtestReport.accuracy_stats?.accuracy || 0) * 100"
                  :color="getAccuracyColor(backtestReport.accuracy_stats?.accuracy || 0)"
                />
              </el-descriptions-item>
              <el-descriptions-item label="平均价格误差">
                {{ (backtestReport.accuracy_stats?.avg_price_error || 0) * 100 | toFixed(2) }}%
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="backtestReport.accuracy_stats?.confidence_accuracy" class="confidence-section">
              <h4>📊 按置信度统计</h4>
              <el-row :gutter="20">
                <el-col
                  v-for="(stats, bucket) in backtestReport.accuracy_stats.confidence_accuracy"
                  :key="bucket"
                  :span="8"
                >
                  <el-card shadow="hover">
                    <div class="confidence-bucket">
                      <h5>{{ bucket }}</h5>
                      <p>总数: {{ stats.total }}</p>
                      <p>正确: {{ stats.correct }}</p>
                      <el-progress
                        :percentage="stats.accuracy * 100"
                        :color="getAccuracyColor(stats.accuracy)"
                      />
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
            
            <div v-if="backtestReport.recent_predictions?.length > 0" class="recent-section">
              <h4>🕒 最近预测</h4>
              <el-table :data="backtestReport.recent_predictions" stripe max-height="400">
                <el-table-column prop="datetime" label="时间" width="180" />
                <el-table-column prop="symbol" label="交易对" width="120" />
                <el-table-column label="预测方向" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getDirectionType(row.prediction?.direction)">
                      {{ getDirectionLabel(row.prediction?.direction) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="置信度" width="120">
                  <template #default="{ row }">
                    {{ row.prediction?.confidence?.toFixed(1) }}%
                  </template>
                </el-table-column>
                <el-table-column label="验证状态" width="120">
                  <template #default="{ row }">
                    <el-tag :type="row.verified ? 'success' : 'info'">
                      {{ row.verified ? '已验证' : '待验证' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="结果" width="100">
                  <template #default="{ row }">
                    <span v-if="row.verified">
                      <el-tag :type="row.verification_result?.direction_correct ? 'success' : 'danger'">
                        {{ row.verification_result?.direction_correct ? '✓ 正确' : '✗ 错误' }}
                      </el-tag>
                    </span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
          <el-empty v-else description="请先运行模拟回测或查看报告" />
        </el-tab-pane>
        
        <el-tab-pane label="预测历史" name="history">
          <div class="history-panel">
            <el-row :gutter="20" class="filter-row">
              <el-col :span="6">
                <el-input
                  v-model="historyFilter.symbol"
                  placeholder="交易对（可选）"
                  clearable
                />
              </el-col>
              <el-col :span="6">
                <el-select
                  v-model="historyFilter.verified"
                  placeholder="验证状态"
                  clearable
                >
                  <el-option :label="全部" :value="null" />
                  <el-option label="已验证" :value="true" />
                  <el-option label="待验证" :value="false" />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-button @click="getPredictionsHistory">
                  查询
                </el-button>
              </el-col>
            </el-row>
            
            <el-table :data="predictionsHistory" stripe>
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
              <el-table-column label="验证" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.verified ? 'success' : 'info'">
                    {{ row.verified ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="记录预测" name="record">
          <div class="record-panel">
            <el-form :model="predictionForm" label-width="120px">
              <el-form-item label="交易对">
                <el-input v-model="predictionForm.symbol" placeholder="如：BTCUSDT" />
              </el-form-item>
              <el-form-item label="预测方向">
                <el-select v-model="predictionForm.prediction.direction" placeholder="选择方向">
                  <el-option label="看涨 📈" value="up" />
                  <el-option label="看跌 📉" value="down" />
                  <el-option label="震荡 ➡️" value="sideways" />
                </el-select>
              </el-form-item>
              <el-form-item label="置信度">
                <el-slider
                  v-model="predictionForm.prediction.confidence"
                  :min="0"
                  :max="100"
                  :show-input
                />
              </el-form-item>
              <el-form-item label="预测价格（可选）">
                <el-input-number v-model="predictionForm.prediction.predicted_price" :min="0" :step="0.0001" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="recordPrediction">
                  记录预测
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="验证预测" name="verify">
          <div class="verify-panel">
            <el-form :model="verifyForm" label-width="120px">
              <el-form-item label="预测ID">
                <el-input-number v-model="verifyForm.prediction_id" :min="1" />
              </el-form-item>
              <el-form-item label="实际价格">
                <el-input-number v-model="verifyForm.actual_price" :min="0" :step="0.0001" />
              </el-form-item>
              <el-form-item label="实际方向（可选）">
                <el-select v-model="verifyForm.actual_direction" placeholder="选择方向" clearable>
                  <el-option label="上涨" value="up" />
                  <el-option label="下跌" value="down" />
                  <el-option label="震荡" value="sideways" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="verifyPrediction">
                  验证预测
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const symbol = ref('BTCUSDT')
const activeTab = ref('report')
const backtestReport = ref<any>(null)
const predictionsHistory = ref<any[]>([])

const predictionForm = reactive({
  symbol: '',
  prediction: {
    direction: '',
    confidence: 50,
    predicted_price: null
  }
})

const verifyForm = reactive({
  prediction_id: 1,
  actual_price: 0,
  actual_direction: ''
})

const historyFilter = reactive({
  symbol: '',
  verified: null
})

const runMockBacktest = async () => {
  try {
    ElMessage.info(`正在运行 ${symbol.value} 的模拟回测...`)
    // TODO: 调用 API
    // const response = await fetch(`/api/prediction-backtest/mock/${symbol.value}?num_predictions=50`)
    // const data = await response.json()
    // backtestReport.value = data.data?.report
    ElMessage.success('模拟回测完成！')
  } catch (error) {
    ElMessage.error('模拟回测失败')
  }
}

const getReport = async () => {
  try {
    ElMessage.info('正在获取回测报告...')
    // TODO: 调用 API
    // const response = await fetch(`/api/prediction-backtest/report/${symbol.value}`)
    // const data = await response.json()
    // backtestReport.value = data.data
    ElMessage.success('报告已获取！')
  } catch (error) {
    ElMessage.error('获取报告失败')
  }
}

const getPredictionsHistory = async () => {
  try {
    ElMessage.info('正在查询预测历史...')
    // TODO: 调用 API
    // const response = await fetch(`/api/prediction-backtest/predictions?symbol=${historyFilter.symbol}&verified=${historyFilter.verified}`)
    // const data = await response.json()
    // predictionsHistory.value = data.data
    ElMessage.success('查询完成！')
  } catch (error) {
    ElMessage.error('查询失败')
  }
}

const recordPrediction = async () => {
  try {
    ElMessage.info('正在记录预测...')
    // TODO: 调用 API
    // const response = await fetch('/api/prediction-backtest/record', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(predictionForm)
    // })
    ElMessage.success('预测已记录！')
  } catch (error) {
    ElMessage.error('记录失败')
  }
}

const verifyPrediction = async () => {
  try {
    ElMessage.info('正在验证预测...')
    // TODO: 调用 API
    // const response = await fetch('/api/prediction-backtest/verify', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(verifyForm)
    // })
    ElMessage.success('验证完成！')
  } catch (error) {
    ElMessage.error('验证失败')
  }
}

const getGradeType = (grade: string) => {
  if (grade === 'S' || grade === 'A') return 'success'
  if (grade === 'B') return 'warning'
  return 'danger'
}

const getAccuracyColor = (accuracy: number) => {
  if (accuracy >= 0.8) return '#67C23A'
  if (accuracy >= 0.6) return '#E6A23C'
  return '#F56C6C'
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
</script>

<style scoped>
.prediction-backtest-container {
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

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.report-header h3 {
  margin: 0;
}

.report-stats {
  margin-bottom: 30px;
}

.confidence-section,
.recent-section {
  margin-top: 30px;
}

.confidence-section h4,
.recent-section h4 {
  margin-bottom: 15px;
}

.confidence-bucket {
  text-align: center;
}

.filter-row {
  margin-bottom: 20px;
}

.record-panel,
.verify-panel {
  max-width: 600px;
  margin: 0 auto;
}
</style>
