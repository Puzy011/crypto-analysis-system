<template>
  <div class="prediction">
    <el-row :gutter="20">
      <!-- 左侧：预测设置 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔮 预测设置</span>
            </div>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="币种">
              <el-select v-model="symbol" @change="loadPrediction">
                <el-option
                  v-for="item in symbolOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时间周期">
              <el-select v-model="interval" @change="loadPrediction">
                <el-option label="1小时" value="1h" />
                <el-option label="4小时" value="4h" />
                <el-option label="1天" value="1d" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="预测区间">
              <el-select v-model="horizon" @change="loadPrediction">
                <el-option label="6小时" :value="6" />
                <el-option label="12小时" :value="12" />
                <el-option label="24小时" :value="24" />
                <el-option label="48小时" :value="48" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="loadPrediction" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新预测
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧：预测结果 -->
      <el-col :span="16">
        <!-- 趋势预测 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>📈 趋势预测</span>
              <el-tag v-if="trendPrediction" :type="getTrendTagType(trendPrediction.prediction)">
                {{ getTrendText(trendPrediction.prediction) }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="!trendPrediction" class="loading">
            <el-skeleton :rows="5" animated />
          </div>
          
          <div v-else class="prediction-result">
            <div class="confidence-bar">
              <div class="label">预测置信度</div>
              <el-progress 
                :percentage="Math.round(trendPrediction.confidence * 100)" 
                :color="getConfidenceColor(trendPrediction.confidence)"
              />
            </div>
            
            <el-divider />
            
            <div class="signals">
              <div class="signal-item">
                <span class="label">看涨信号</span>
                <el-tag type="success">{{ trendPrediction.signals.bullish_count }}</el-tag>
              </div>
              <div class="signal-item">
                <span class="label">看跌信号</span>
                <el-tag type="danger">{{ trendPrediction.signals.bearish_count }}</el-tag>
              </div>
              <div class="signal-item">
                <span class="label">总信号数</span>
                <el-tag type="info">{{ trendPrediction.signals.total_signals }}</el-tag>
              </div>
            </div>
            
            <el-divider />
            
            <div class="levels">
              <div class="level-item">
                <span class="label">当前价格</span>
                <span class="value">${{ trendPrediction.current_price.toLocaleString() }}</span>
              </div>
              <div class="level-item" v-if="trendPrediction.levels.support">
                <span class="label">支撑位</span>
                <span class="value support">${{ trendPrediction.levels.support.toLocaleString() }}</span>
              </div>
              <div class="level-item" v-if="trendPrediction.levels.resistance">
                <span class="label">阻力位</span>
                <span class="value resistance">${{ trendPrediction.levels.resistance.toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 价格区间预测 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 价格区间预测 ({{ horizon }}小时)</span>
              <el-tag type="info">{{ rangePrediction?.confidence_level }}</el-tag>
            </div>
          </template>
          
          <div v-if="!rangePrediction" class="loading">
            <el-skeleton :rows="4" animated />
          </div>
          
          <div v-else class="range-result">
            <div class="range-display">
              <div class="range-item lower">
                <div class="label">下限</div>
                <div class="value">${{ rangePrediction.lower_bound.toLocaleString() }}</div>
              </div>
              <div class="range-divider">—</div>
              <div class="range-item upper">
                <div class="label">上限</div>
                <div class="value">${{ rangePrediction.upper_bound.toLocaleString() }}</div>
              </div>
            </div>
            
            <el-divider />
            
            <div class="range-info">
              <div class="info-item">
                <span class="label">当前价格</span>
                <span class="value">${{ rangePrediction.current_price.toLocaleString() }}</span>
              </div>
              <div class="info-item">
                <span class="label">历史波动率</span>
                <span class="value">{{ (rangePrediction.volatility * 100).toFixed(2) }}%</span>
              </div>
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
import { SYMBOLS } from '@/constants'

const symbol = ref('BTCUSDT')
const symbolOptions = SYMBOLS
const interval = ref('1h')
const horizon = ref(24)
const loading = ref(false)
const trendPrediction = ref<any>(null)
const rangePrediction = ref<any>(null)

const loadPrediction = async () => {
  loading.value = true
  
  try {
    // 加载趋势预测
    const trendResponse = await axios.get(`/api/prediction/trend/${symbol.value}`, {
      params: { interval: interval.value }
    })
    if (trendResponse.data.success) {
      trendPrediction.value = trendResponse.data.data
    }
    
    // 加载价格区间预测
    const rangeResponse = await axios.get(`/api/prediction/range/${symbol.value}`, {
      params: { interval: interval.value, horizon: horizon.value }
    })
    if (rangeResponse.data.success) {
      rangePrediction.value = rangeResponse.data.data
    }
  } catch (error) {
    console.error('加载预测失败:', error)
    ElMessage.error('加载预测失败')
  } finally {
    loading.value = false
  }
}

const getTrendText = (prediction: string): string => {
  const texts: Record<string, string> = {
    up: '看涨 📈',
    down: '看跌 📉',
    sideways: '震荡 ➡️'
  }
  return texts[prediction] || prediction
}

const getTrendTagType = (prediction: string): string => {
  const types: Record<string, string> = {
    up: 'success',
    down: 'danger',
    sideways: 'warning'
  }
  return types[prediction] || 'info'
}

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.7) return '#67c23a'
  if (confidence >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadPrediction()
})
</script>

<style scoped>
.prediction {
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

.prediction-result {
  padding: 10px 0;
}

.confidence-bar {
  margin-bottom: 20px;
}

.confidence-bar .label {
  display: block;
  margin-bottom: 8px;
  color: #606266;
}

.signals {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}

.signal-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.signal-item .label {
  color: #909399;
  font-size: 13px;
}

.levels {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}

.level-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.level-item .label {
  color: #909399;
  font-size: 13px;
}

.level-item .value {
  font-size: 18px;
  font-weight: 600;
}

.level-item .value.support {
  color: #67c23a;
}

.level-item .value.resistance {
  color: #f56c6c;
}

.range-result {
  padding: 10px 0;
}

.range-display {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 20px 0;
}

.range-item {
  text-align: center;
  padding: 15px 30px;
  border-radius: 8px;
}

.range-item.lower {
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
}

.range-item.upper {
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
}

.range-item .label {
  display: block;
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.range-item .value {
  font-size: 24px;
  font-weight: 700;
}

.range-item.lower .value {
  color: #f56c6c;
}

.range-item.upper .value {
  color: #409eff;
}

.range-divider {
  font-size: 24px;
  color: #909399;
  font-weight: 300;
}

.range-info {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  color: #909399;
  font-size: 13px;
}

.info-item .value {
  font-size: 16px;
  font-weight: 600;
}
</style>
