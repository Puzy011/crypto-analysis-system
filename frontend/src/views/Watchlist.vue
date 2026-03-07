<template>
  <div class="watchlist">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>⭐ 自选币</span>
          <el-tag type="info">{{ watchlistStore.watchlist.length }} 个币种</el-tag>
        </div>
      </template>
      
      <div v-if="watchlistStore.watchlist.length === 0" class="empty-state">
        <el-empty description="暂无自选币，去市场添加吧！">
          <el-button type="primary" @click="$router.push('/market')">
            去市场
          </el-button>
        </el-empty>
      </div>
      
      <el-table v-else :data="watchlistTickers" style="width: 100%" @row-click="goToDetail">
        <el-table-column width="60">
          <template #default="{ row }">
            <el-button 
              type="danger" 
              size="small"
              circle
              @click.stop="removeFromWatchlist(row.symbol)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="币种" width="120" />
        <el-table-column prop="price" label="价格" width="140">
          <template #default="{ row }">
            <span v-if="row.price">${{ row.price.toLocaleString() }}</span>
            <span v-else class="loading">加载中...</span>
          </template>
        </el-table-column>
        <el-table-column prop="priceChangePercent" label="24h涨跌" width="120">
          <template #default="{ row }">
            <el-tag 
              v-if="row.priceChangePercent !== undefined"
              :type="row.priceChangePercent >= 0 ? 'success' : 'danger'"
            >
              {{ row.priceChangePercent >= 0 ? '+' : '' }}{{ row.priceChangePercent.toFixed(2) }}%
            </el-tag>
            <span v-else class="loading">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="goToDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWatchlistStore } from '@/stores/watchlist'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const watchlistStore = useWatchlistStore()
const watchlistTickers = ref<any[]>([])

const loadWatchlistTickers = async () => {
  if (watchlistStore.watchlist.length === 0) {
    watchlistTickers.value = []
    return
  }
  
  const symbols = watchlistStore.watchlist.map(item => item.symbol).join(',')
  
  try {
    const response = await axios.get('/api/market/tickers', {
      params: { symbols }
    })
    if (response.data.success) {
      // 按自选顺序排序
      const symbolMap = new Map(
        response.data.data.map((t: any) => [t.symbol, t])
      )
      watchlistTickers.value = watchlistStore.watchlist.map(item => ({
        ...item,
        ...(symbolMap.get(item.symbol) || {})
      }))
    }
  } catch (error) {
    console.error('加载自选行情失败:', error)
  }
}

const removeFromWatchlist = async (symbol: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消自选 ${symbol} 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    watchlistStore.removeFromWatchlist(symbol)
    ElMessage.success(`已取消自选 ${symbol}`)
  } catch {
    // 用户取消
  }
}

const goToDetail = (row: any) => {
  router.push({ 
    path: '/market', 
    query: { symbol: row.symbol } 
  })
}

// 监听自选变化，重新加载
watch(
  () => watchlistStore.watchlist,
  () => {
    loadWatchlistTickers()
  },
  { deep: true }
)

onMounted(() => {
  loadWatchlistTickers()
  // 每30秒刷新一次
  setInterval(loadWatchlistTickers, 30000)
})
</script>

<style scoped>
.watchlist {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
}

.loading {
  color: #909399;
}
</style>
