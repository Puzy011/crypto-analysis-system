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
            <el-form-item label="市场">
              <el-radio-group v-model="marketType" size="small" @change="handleMarketChange">
                <el-radio-button label="spot">现货</el-radio-button>
                <el-radio-button label="futures">合约</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="币种">
              <el-select v-model="symbol" @change="loadAnalysis">
                <el-option
                  v-for="item in symbolOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="最近查询" v-if="recentQueries.length">
              <div class="recent-tags">
                <el-tag
                  v-for="(item, idx) in recentQueries.slice(0, 6)"
                  :key="`rq-${idx}`"
                  @click="applyRecentQuery(item)"
                >
                  {{ item.symbol }} · {{ item.market_type === 'futures' ? '合约' : '现货' }}
                </el-tag>
              </div>
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
        <!-- 报告摘要 -->
        <el-card v-if="report" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>🧾 报告摘要</span>
              <el-button size="small" @click="copyShare" :disabled="!shareText">
                复制分享
              </el-button>
            </div>
          </template>

          <div class="report-note" v-if="report.mode_note">
            {{ report.mode_note }}
          </div>

          <div class="report-grid">
            <div class="report-item">
              <span class="label">庄家方向</span>
              <span class="value">{{ report.direction || '-' }}</span>
            </div>
            <div class="report-item">
              <span class="label">庄家动作</span>
              <span class="value">{{ report.action || '-' }}</span>
            </div>
            <div class="report-item">
              <span class="label">交易建议</span>
              <span class="value">{{ report.advice || '-' }}</span>
            </div>
            <div class="report-item">
              <span class="label">风险控制</span>
              <span class="value">{{ report.risk_control || '-' }}</span>
            </div>
          </div>

          <el-divider />

          <div class="report-grid" v-if="report.key_levels">
            <div class="report-item">
              <span class="label">参考入场</span>
              <span class="value">{{ formatPrice(report.key_levels.entry) }}</span>
            </div>
            <div class="report-item">
              <span class="label">止损位</span>
              <span class="value">{{ formatPrice(report.key_levels.stop_loss) }}</span>
            </div>
            <div class="report-item">
              <span class="label">止盈位</span>
              <span class="value">{{ formatPrice(report.key_levels.take_profit) }}</span>
            </div>
            <div class="report-item">
              <span class="label">置信度</span>
              <span class="value">{{ ((report.confidence || 0) * 100).toFixed(0) }}%</span>
            </div>
          </div>

          <div class="report-points" v-if="report.entry_conditions?.length || report.invalidation_conditions?.length">
            <div v-for="(point, idx) in report.entry_conditions || []" :key="`entry-${idx}`" class="report-point">
              触发条件: {{ point }}
            </div>
            <div v-for="(point, idx) in report.invalidation_conditions || []" :key="`invalid-${idx}`" class="report-point">
              失效条件: {{ point }}
            </div>
          </div>
        </el-card>

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
import { SYMBOLS } from '@/constants'

const symbol = ref('BTCUSDT')
const interval = ref('1h')
const marketType = ref<'spot' | 'futures'>('spot')
const symbolOptions = ref<Array<{ label: string; value: string }>>([...SYMBOLS])
const loading = ref(false)
const whaleAnalysis = ref<any>(null)
const report = ref<any>(null)
const shareText = ref('')
const recentQueries = ref<any[]>([])

const mergeSymbolOptions = (
  primary: Array<{ label: string; value: string }>,
  fallback: Array<{ label: string; value: string }>
) => {
  const merged: Array<{ label: string; value: string }> = []
  const seen = new Set<string>()
  for (const item of [...primary, ...fallback]) {
    if (!item?.value || seen.has(item.value)) continue
    seen.add(item.value)
    merged.push(item)
  }
  return merged
}

const fetchSymbolOptions = async () => {
  try {
    const response = await axios.get('/api/market/symbols', {
      params: {
        quote_asset: 'USDT',
        limit: 500,
        market_type: marketType.value
      }
    })
    if (response.data?.success && Array.isArray(response.data.data)) {
      const rows = response.data.data
      if (!rows.length) {
        symbolOptions.value = [...SYMBOLS]
      } else {
        const dynamicOptions = rows.map((row: any) => {
          const symbolValue = String(row.symbol || '')
          if (symbolValue.endsWith('USDT')) {
            return { value: symbolValue, label: `${symbolValue.slice(0, -4)}/USDT` }
          }
          return { value: symbolValue, label: symbolValue }
        })
        symbolOptions.value = mergeSymbolOptions(dynamicOptions, SYMBOLS)
      }
    } else {
      symbolOptions.value = [...SYMBOLS]
    }
  } catch (error) {
    symbolOptions.value = [...SYMBOLS]
    console.error('获取交易对列表失败:', error)
  }

  const exists = symbolOptions.value.some(item => item.value === symbol.value)
  if (!exists && symbolOptions.value.length > 0) {
    symbol.value = symbolOptions.value[0].value
  }
}

const loadAnalysis = async () => {
  loading.value = true
  
  try {
    const tradeType = getTradeTypeByInterval(interval.value)
    const [baseRes, reportRes] = await Promise.all([
      axios.get(`/api/whale/analyze/${symbol.value}`, {
        params: { interval: interval.value, market_type: marketType.value }
      }),
      axios.get(`/api/whale-analysis/full/${symbol.value}`, {
        params: { trade_type: tradeType, market_type: marketType.value }
      })
    ])
    if (baseRes.data?.success) {
      whaleAnalysis.value = baseRes.data.data
    }
    if (reportRes.data?.success) {
      report.value = reportRes.data.report || null
      shareText.value = reportRes.data.share_text || ''
      recentQueries.value = reportRes.data.recent_queries || []
    }
  } catch (error) {
    console.error('加载庄家分析失败:', error)
    ElMessage.error('加载庄家分析失败')
  } finally {
    loading.value = false
  }
}

const handleMarketChange = async () => {
  await fetchSymbolOptions()
  await loadAnalysis()
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

const formatPrice = (value: any): string => {
  if (value == null || value === '') return '-'
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toFixed(value >= 1 ? 2 : 6)
  }
  return String(value)
}

const getTradeTypeByInterval = (value: string): string => {
  if (value === '1h') return 'intraday'
  if (value === '4h' || value === '1d') return 'longterm'
  return 'realtime'
}

const copyShare = async () => {
  if (!shareText.value) return
  try {
    await navigator.clipboard.writeText(shareText.value)
    ElMessage.success('分享内容已复制')
  } catch (error) {
    console.error('复制分享失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

const applyRecentQuery = (item: any) => {
  if (!item) return
  if (item.symbol) symbol.value = item.symbol
  if (item.market_type) marketType.value = item.market_type
  loadAnalysis()
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSymbolOptions().finally(() => {
    loadAnalysis()
  })
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

.recent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.recent-tags .el-tag {
  cursor: pointer;
}

.report-note {
  color: #606266;
  font-size: 13px;
  margin-bottom: 12px;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.report-item {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.report-item .label {
  color: #909399;
  font-size: 12px;
}

.report-item .value {
  font-weight: 600;
  color: #303133;
}

.report-points {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-point {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  color: #1f2937;
}
</style>
