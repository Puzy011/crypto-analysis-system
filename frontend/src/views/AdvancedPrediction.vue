<template>
  <div class="advanced-prediction">
    <div class="page-header">
      <h1>🤖 高级预测</h1>
      <p>基于 XGBoost、LightGBM、Prophet 的多模型融合预测</p>
    </div>

    <!-- 模型训练区域 -->
    <div class="card">
      <h3>🎯 模型训练</h3>
      <div class="train-controls">
        <select v-model="selectedSymbol" class="input-select">
          <option value="BTCUSDT">BTC/USDT</option>
          <option value="ETHUSDT">ETH/USDT</option>
          <option value="BNBUSDT">BNB/USDT</option>
        </select>
        <select v-model="targetHorizon" class="input-select">
          <option value="1h">1小时预测</option>
          <option value="4h">4小时预测</option>
          <option value="24h">24小时预测</option>
        </select>
        <button @click="trainModels" class="btn btn-primary" :disabled="isTraining">
          {{ isTraining ? '训练中...' : '开始训练' }}
        </button>
      </div>
    </div>

    <!-- 预测结果 -->
    <div class="card" v-if="prediction">
      <h3>📊 预测结果</h3>
      <div class="prediction-result">
        <div class="prediction-main">
          <div class="prediction-direction" :class="prediction.direction">
            {{ prediction.direction === 'up' ? '🚀 看涨' : prediction.direction === 'down' ? '🔻 看跌' : '➡️ 震荡' }}
          </div>
          <div class="prediction-confidence">
            置信度: {{ (prediction.confidence * 100).toFixed(1) }}%
          </div>
          <div class="prediction-return">
            预期收益: {{ (prediction.predicted_return * 100).toFixed(2) }}%
          </div>
        </div>

        <div class="model-predictions">
          <h4>各模型预测</h4>
          <div class="model-list">
            <div v-for="(pred, model) in prediction.individual_predictions" :key="model" class="model-item">
              <span class="model-name">{{ model }}</span>
              <span class="model-pred">{{ (pred * 100).toFixed(2) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 特征重要性 -->
    <div class="card" v-if="topFeatures && Object.keys(topFeatures).length > 0">
      <h3>🔍 特征重要性</h3>
      <div class="features-grid">
        <div v-for="(features, model) in topFeatures" :key="model" class="feature-card">
          <h4>{{ model }}</h4>
          <div class="feature-list">
            <div v-for="(feat, idx) in features" :key="idx" class="feature-item">
              <span class="feature-name">{{ feat.feature }}</span>
              <div class="feature-bar">
                <div class="feature-bar-fill" :style="{ width: (feat.importance * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 预测历史 -->
    <div class="card">
      <h3>📜 预测历史</h3>
      <div class="history-list">
        <div v-for="(record, idx) in predictionHistory" :key="idx" class="history-item">
          <span class="history-time">{{ formatTime(record.timestamp) }}</span>
          <span class="history-symbol">{{ record.symbol }}</span>
          <span class="history-direction" :class="record.final_direction">
            {{ record.final_label }}
          </span>
          <span class="history-conf">{{ (record.final_confidence * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const selectedSymbol = ref('BTCUSDT')
const targetHorizon = ref('1h')
const isTraining = ref(false)
const prediction = ref<any>(null)
const topFeatures = ref<any>({})
const predictionHistory = ref<any[]>([])

const apiBase = '/api'

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString('zh-CN')
}

const trainModels = async () => {
  isTraining.value = true
  try {
    const response = await fetch(`${apiBase}/advanced-prediction/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: selectedSymbol.value,
        target_horizon: targetHorizon.value,
        use_xgboost: true,
        use_lightgbm: true,
        use_random_forest: true,
        use_prophet: true
      })
    })
    const data = await response.json()
    console.log('训练完成:', data)
    await getPrediction()
  } catch (error) {
    console.error('训练失败:', error)
  } finally {
    isTraining.value = false
  }
}

const getPrediction = async () => {
  try {
    const response = await fetch(
      `${apiBase}/advanced-prediction/predict/${selectedSymbol.value}?target_horizon=${targetHorizon.value}`
    )
    prediction.value = await response.json()
    
    const featResponse = await fetch(`${apiBase}/advanced-prediction/features/${selectedSymbol.value}`)
    const featData = await featResponse.json()
    topFeatures.value = featData.feature_importance || {}
  } catch (error) {
    console.error('获取预测失败:', error)
  }
}

onMounted(() => {
  getPrediction()
})
</script>

<style scoped>
.advanced-prediction {
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

.train-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.input-select {
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  min-width: 150px;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
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

.prediction-result {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.prediction-main {
  text-align: center;
  padding: 24px;
  background: #f8f9ff;
  border-radius: 12px;
}

.prediction-direction {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 12px;
}

.prediction-direction.up {
  color: #10b981;
}

.prediction-direction.down {
  color: #ef4444;
}

.prediction-confidence,
.prediction-return {
  font-size: 16px;
  color: #666;
  margin: 8px 0;
}

.model-predictions h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.model-name {
  color: #666;
}

.model-pred {
  font-weight: 600;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.feature-card {
  background: #f8f9ff;
  padding: 16px;
  border-radius: 12px;
}

.feature-card h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-name {
  font-size: 12px;
  color: #666;
  min-width: 120px;
}

.feature-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.feature-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: grid;
  grid-template-columns: 180px 100px 1fr 100px;
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

.history-symbol {
  font-weight: 600;
}

.history-direction.up {
  color: #10b981;
}

.history-direction.down {
  color: #ef4444;
}

.history-conf {
  color: #666;
}

@media (max-width: 768px) {
  .prediction-result {
    grid-template-columns: 1fr;
  }
  
  .history-item {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
}
</style>

