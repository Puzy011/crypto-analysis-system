<template>
  <div class="whale">
    <el-row :gutter="20">
      <!-- 左侧：分析设置 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🕵️ 庄家分析设置</span>
            </div>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="币种">
              <el-select v-model="symbol" @change="loadAnalysis">
                <el-option label="BTC/USDT" value="BTCUSDT" />
                <el-option label="ETH/USDT" value="ETHUSDT" />
                <el-option label="BNB/USDT" value="BNBUSDT" />
                <el-option label="SOL/USDT" value="SOLUSDT" />
                <el-option label="XRP/USDT" value="XRPUSDT" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时间周期">
              <el-select v-model="interval" @change="loadAnalysis">
                <el-option label="1小时" value="1h" />
                <el-option label="4小时" value="4h" />
                <el-option label="1天" value="1d" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="loadAnalysis" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧：分析结果 -->
      <el-col :span="16">
        <!-- 阶段识别 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>📊 当前市场阶段</span>
              <el-tag v-if="whaleAnalysis" :type="getPhaseTagType(whaleAnalysis.phase.phase)">
                {{ getPhaseText(whaleAnalysis.phase.phase) }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="!whaleAnalysis" class="loading">
            <el-skeleton :rows="5" animated />
          </div>
          
          <div v-else class="phase-result">
            <div class="confidence-bar">
              <div class="label">识别置信度</div>
              <el-progress 
                :percentage="Math.round(whaleAnalysis.phase.confidence * 100)" 
                :color="getConfidenceColor(whaleAnalysis.phase.confidence)"
              />
            </div>
            
            <el-divider />
            
            <div class="phase-signals">
              <div class="signal-title">识别信号：</div>
              <el-tag 
                v-for="(signal, index) in whaleAnalysis.phase.signals" 
                :key="index"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ signal }}
              </el-tag>
              <div v-if="whaleAnalysis.phase.signals.length === 0" class="no-signals">
                暂无明显信号
              </div>
            </div>
            
            <el-divider />
            
            <div class="phase-indicators">
              <div class="indicator-item">
                <span class="label">20周期涨跌幅</span>
                <span class="value" :class="whaleAnalysis.phase.indicators.price_change_20 >= 0 ? 'up' : 'down'">
                  {{ (whaleAnalysis.phase.indicators.price_change_20 * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="indicator-item">
                <span class="label">成交量比率</span>
                <span class="value">{{ whaleAnalysis.phase.indicators.volume_ratio.toFixed(2) }}x</span>
              </div>
              <div class="indicator-item">
                <span class="label">波动率</span>
                <span class="value">{{ (whaleAnalysis.phase.indicators.volatility * 100).toFixed(2) }}%</span>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 资金流向 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>💸 资金流向</span>
              <el-tag v-if="whaleAnalysis" :type="getFlowTagType(whaleAnalysis.money_flow.overall)">
                {{ getFlowText(whaleAnalysis.money_flow.overall) }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="!whaleAnalysis" class="loading">
            <el-skeleton :rows="4" animated />
          </div>
          
          <div v-else class="flow-result">
            <el-row :gutter="20">
              <el-col v-for="(periodData, periodKey) in whaleAnalysis.money_flow.periods" :key="periodKey" :span="12">
                <el-card shadow="hover" size="small">
                  <template #header>
                    <span>{{ periodKey }}周期</span>
                  </template>
                  <div class="flow-item">
                    <div class="flow-label">资金流入</div>
                    <div class="flow-value inflow">{{ formatVolume(periodData.inflow) }}</div>
                  </div>
                  <div class="flow-item">
                    <div class="flow-label">资金流出</div>
                    <div class="flow-value outflow">{{ formatVolume(periodData.outflow) }}</div>
                  </div>
                  <el-divider />
                  <div class="flow-item">
                    <div class="flow-label">净流入</div>
                    <div class="flow-value" :class="periodData.net_flow >= 0 ? 'inflow' : 'outflow'">
                      {{ formatVolume(periodData.net_flow) }}
                    </div>
                  </div>
                  <div class="flow-item">
                    <div class="flow-label">流入占比</div>
                    <el-progress 
                      :percentage="Math.round(periodData.inflow_ratio * 100)" 
                      :color="getFlowProgressColor(periodData.inflow_ratio)"
                      :stroke-width="12"
                    />
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-card>
        
        <!-- 大单检测 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 大单检测</span>
              <el-tag type="info">{{ whaleAnalysis?.large_orders_count || 0 }} 个大单</el-tag>
            </div>
          </template>
          
          <div v-if="!whaleAnalysis" class="loading">
            <el-skeleton :rows="4" animated />
          </div>
          
          <div v-else-if="whaleAnalysis.large_orders.length === 0" class="empty-state">
            <el-empty description="暂无大单数据" />
          </div>
          
          <el-table v-else :data="whaleAnalysis.large_orders" style="width: 100%">
            <el-table-column label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column label="价格" width="140">
              <template #default="{ row }">
                <span v-if="row.price">${{ row.price.toLocaleString() }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="成交量" width="160">
              <template #default="{ row }">
                {{ formatVolume(row.volume) }}
              </template>
            </el-table-column>
            <el-table-column label="方向" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_buy ? 'success' : 'danger'" size="small">
                  {{ row.is_buy ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
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

const symbol = ref('BTCUSDT')
const interval = ref('1h')
const loading = ref(false)
const whaleAnalysis = ref<any>(null)

const loadAnalysis = async () => {
  loading.value = true
  
  try {
    const response = await axios.get(`/api/whale/analyze/${symbol.value}`, {
      params: { interval: interval.value }
    })
    if (response.data.success) {
      whaleAnalysis.value = response.data.data
    }
  } catch (error) {
    console.error('加载庄家分析失败:', error)
    ElMessage.error('加载庄家分析失败')
  } finally {
    loading.value = false
  }
}

const getPhaseText = (phase: string): string => {
  const texts: Record<string, string> = {
    accumulation: '吸筹阶段 📦',
    washout: '洗盘阶段 🌊',
    pump: '拉升阶段 🚀',
    distribution: '出货阶段 📦',
    unknown: '未知阶段 ❓'
  }
  return texts[phase] || phase
}

const getPhaseTagType = (phase: string): string => {
  const types: Record<string, string> = {
    accumulation: 'info',
    washout: 'warning',
    pump: 'success',
    distribution: 'danger',
    unknown: ''
  }
  return types[phase] || ''
}

const getFlowText = (flow: string): string => {
  const texts: Record<string, string> = {
    inflow: '资金流入 📈',
    outflow: '资金流出 📉',
    neutral: '资金平衡 ➡️'
  }
  return texts[flow] || flow
}

const getFlowTagType = (flow: string): string => {
  const types: Record<string, string> = {
    inflow: 'success',
    outflow: 'danger',
    neutral: 'warning'
  }
  return types[flow] || ''
}

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.7) return '#67c23a'
  if (confidence >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

const getFlowProgressColor = (ratio: number): string => {
  if (ratio >= 0.6) return '#67c23a'
  if (ratio >= 0.4) return '#e6a23c'
  return '#f56c6c'
}

const formatVolume = (volume: number): string => {
  if (volume >= 1000000000) {
    return (volume / 1000000000).toFixed(2) + 'B'
  }
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(2) + 'M'
  }
  if (volume >= 1000) {
    return (volume / 1000).toFixed(2) + 'K'
  }
  return volume.toFixed(2)
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAnalysis()
})
</script>

<style scoped>
.whale {
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

.phase-result {
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

.phase-signals {
  margin-bottom: 20px;
}

.signal-title {
  color: #606266;
  margin-bottom: 10px;
}

.no-signals {
  color: #909399;
  font-size: 14px;
}

.phase-indicators {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.indicator-item .label {
  color: #909399;
  font-size: 13px;
}

.indicator-item .value {
  font-size: 18px;
  font-weight: 600;
}

.indicator-item .value.up {
  color: #67c23a;
}

.indicator-item .value.down {
  color: #f56c6c;
}

.flow-result {
  padding: 10px 0;
}

.flow-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.flow-label {
  color: #606266;
  font-size: 14px;
}

.flow-value {
  font-size: 16px;
  font-weight: 600;
}

.flow-value.inflow {
  color: #67c23a;
}

.flow-value.outflow {
  color: #f56c6c;
}

.empty-state {
  padding: 40px 0;
}
</style>
