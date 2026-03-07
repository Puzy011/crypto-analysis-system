<template>
  <div class="market">
    <el-row :gutter="20">
      <!-- 左侧：行情列表 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📈 市场行情</span>
              <el-button size="small" @click="refreshTickers">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <el-table :data="tickers" style="width: 100%" @row-click="selectSymbol">
            <el-table-column width="60">
              <template #default="{ row }">
                <el-button 
                  :type="watchlistStore.isInWatchlist(row.symbol) ? 'warning' : 'primary'" 
                  size="small"
                  circle
                  @click.stop="toggleWatchlist(row.symbol)"
                >
                  <el-icon><Star /></el-icon>
                </el-button>
              </template>
            </el-table-column>
            <el-table-column prop="symbol" label="币种" width="100" />
            <el-table-column prop="price" label="价格" width="120">
              <template #default="{ row }">
                ${{ row.price.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="priceChangePercent" label="24h涨跌" width="100">
              <template #default="{ row }">
                <el-tag :type="row.priceChangePercent >= 0 ? 'success' : 'danger'">
                  {{ row.priceChangePercent >= 0 ? '+' : '' }}{{ row.priceChangePercent.toFixed(2) }}%
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：K线图 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🕯️ {{ selectedSymbol }} K线图</span>
              <div class="header-controls">
                <el-select v-model="interval" size="small" style="width: 100px; margin-right: 10px;">
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="15分钟" value="15m" />
                  <el-option label="1小时" value="1h" />
                  <el-option label="4小时" value="4h" />
                  <el-option label="1天" value="1d" />
                </el-select>
                <el-button size="small" @click="refreshKlines">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <div ref="chartContainer" class="chart-container"></div>
        </el-card>
        
        <!-- 技术指标面板 -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>📊 技术指标</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <!-- MA 移动平均线 -->
            <el-col :span="8">
              <el-card shadow="hover" size="small">
                <template #header>
                  <span>MA 移动平均线</span>
                </template>
                <div v-if="currentIndicators.ma" class="indicator-list">
                  <div v-for="(values, key) in currentIndicators.ma" :key="key" class="indicator-item">
                    <span class="label">{{ key }}:</span>
                    <span class="value">
                      {{ values[values.length - 1] ? values[values.length - 1].toFixed(2) : '-' }}
                    </span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </el-card>
            </el-col>
            
            <!-- MACD -->
            <el-col :span="8">
              <el-card shadow="hover" size="small">
                <template #header>
                  <span>MACD</span>
                </template>
                <div v-if="currentIndicators.macd" class="indicator-list">
                  <div class="indicator-item">
                    <span class="label">DIF:</span>
                    <span class="value" :class="getValueClass(currentIndicators.macd.DIF?.[currentIndicators.macd.DIF.length - 1])">
                      {{ currentIndicators.macd.DIF?.[currentIndicators.macd.DIF.length - 1]?.toFixed(4) || '-' }}
                    </span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">DEA:</span>
                    <span class="value">
                      {{ currentIndicators.macd.DEA?.[currentIndicators.macd.DEA.length - 1]?.toFixed(4) || '-' }}
                    </span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">MACD:</span>
                    <span class="value" :class="getValueClass(currentIndicators.macd.MACD?.[currentIndicators.macd.MACD.length - 1])">
                      {{ currentIndicators.macd.MACD?.[currentIndicators.macd.MACD.length - 1]?.toFixed(4) || '-' }}
                    </span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </el-card>
            </el-col>
            
            <!-- RSI & KDJ -->
            <el-col :span="8">
              <el-card shadow="hover" size="small">
                <template #header>
                  <span>RSI & KDJ</span>
                </template>
                <div v-if="currentIndicators.rsi && currentIndicators.kdj" class="indicator-list">
                  <div class="indicator-item">
                    <span class="label">RSI(14):</span>
                    <span class="value" :class="getRsiClass(currentIndicators.rsi.RSI?.[currentIndicators.rsi.RSI.length - 1])">
                      {{ currentIndicators.rsi.RSI?.[currentIndicators.rsi.RSI.length - 1]?.toFixed(2) || '-' }}
                    </span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">K:</span>
                    <span class="value">{{ currentIndicators.kdj.K?.[currentIndicators.kdj.K.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">D:</span>
                    <span class="value">{{ currentIndicators.kdj.D?.[currentIndicators.kdj.D.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">J:</span>
                    <span class="value">{{ currentIndicators.kdj.J?.[currentIndicators.kdj.J.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 布林带 -->
          <el-row style="margin-top: 20px;">
            <el-col :span="24">
              <el-card shadow="hover" size="small">
                <template #header>
                  <span>布林带 (BOLL)</span>
                </template>
                <div v-if="currentIndicators.boll" class="indicator-list horizontal">
                  <div class="indicator-item">
                    <span class="label">上轨:</span>
                    <span class="value up">{{ currentIndicators.boll.BOLL_UP?.[currentIndicators.boll.BOLL_UP.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">中轨:</span>
                    <span class="value">{{ currentIndicators.boll.BOLL_MID?.[currentIndicators.boll.BOLL_MID.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="label">下轨:</span>
                    <span class="value down">{{ currentIndicators.boll.BOLL_LOW?.[currentIndicators.boll.BOLL_LOW.length - 1]?.toFixed(2) || '-' }}</span>
                  </div>
                </div>
                <div v-else class="no-data">暂无数据</div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Refresh, Star, Delete } from '@element-plus/icons-vue'
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts'
import axios from 'axios'
import { useWatchlistStore } from '@/stores/watchlist'
import { ElMessage } from 'element-plus'

const tickers = ref<any[]>([])
const selectedSymbol = ref('BTCUSDT')
const interval = ref('1h')
const chartContainer = ref<HTMLElement | null>(null)
const currentIndicators = ref<any>({})

const watchlistStore = useWatchlistStore()

let chart: IChartApi | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null

const refreshTickers = async () => {
  try {
    const response = await axios.get('/api/market/tickers', {
      params: { symbols: 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT' }
    })
    if (response.data.success) {
      tickers.value = response.data.data
    }
  } catch (error) {
    console.error('获取行情失败:', error)
  }
}

const refreshKlines = async () => {
  try {
    const response = await axios.get(`/api/market/klines/${selectedSymbol.value}/indicators`, {
      params: { interval: interval.value, limit: 200 }
    })
    if (response.data.success) {
      updateChart(response.data.data.klines)
      currentIndicators.value = response.data.data.indicators
    }
  } catch (error) {
    console.error('获取K线失败:', error)
  }
}

const selectSymbol = (row: any) => {
  selectedSymbol.value = row.symbol
  refreshKlines()
}

const initChart = () => {
  if (!chartContainer.value) return
  
  chart = createChart(chartContainer.value, {
    width: chartContainer.value.clientWidth,
    height: 400,
    layout: {
      background: { type: 'solid', color: '#ffffff' },
      textColor: '#333',
    },
    grid: {
      vertLines: { color: '#f0f0f0' },
      horzLines: { color: '#f0f0f0' },
    },
  })

  candlestickSeries = chart.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderDownColor: '#ef5350',
    borderUpColor: '#26a69a',
    wickDownColor: '#ef5350',
    wickUpColor: '#26a69a',
  })

  // 响应窗口大小变化
  window.addEventListener('resize', () => {
    if (chart && chartContainer.value) {
      chart.applyOptions({ width: chartContainer.value.clientWidth })
    }
  })
}

const updateChart = (data: any[]) => {
  if (!candlestickSeries) return
  
  const formattedData = data.map((k: any) => ({
    time: k.timestamp / 1000,
    open: k.open,
    high: k.high,
    low: k.low,
    close: k.close,
  }))
  
  candlestickSeries.setData(formattedData)
  
  if (chart) {
    chart.timeScale().fitContent()
  }
}

watch(interval, () => {
  refreshKlines()
})

const getValueClass = (value: number | null | undefined) => {
  if (value == null) return ''
  return value >= 0 ? 'up' : 'down'
}

const getRsiClass = (value: number | null | undefined) => {
  if (value == null) return ''
  if (value > 70) return 'up'
  if (value < 30) return 'down'
  return ''
}

const toggleWatchlist = (symbol: string) => {
  if (watchlistStore.isInWatchlist(symbol)) {
    watchlistStore.removeFromWatchlist(symbol)
    ElMessage.success(`已取消自选 ${symbol}`)
  } else {
    watchlistStore.addToWatchlist(symbol)
    ElMessage.success(`已添加自选 ${symbol}`)
  }
}

onMounted(() => {
  refreshTickers()
  nextTick(() => {
    initChart()
    refreshKlines()
  })
})
</script>

<style scoped>
.market {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.el-table {
  cursor: pointer;
}

.indicator-list {
  max-height: 150px;
  overflow-y: auto;
}

.indicator-list.horizontal {
  display: flex;
  gap: 30px;
  max-height: none;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.indicator-item:last-child {
  border-bottom: none;
}

.label {
  color: #909399;
  font-size: 13px;
}

.value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.value.up {
  color: #67c23a;
}

.value.down {
  color: #f56c6c;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 14px;
}
</style>
