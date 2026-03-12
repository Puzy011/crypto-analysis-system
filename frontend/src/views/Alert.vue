<template>
  <div class="alert">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🔔 价格预警</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加预警
          </el-button>
        </div>
      </template>
      
      <div v-if="alertStore.alerts.length === 0" class="empty-state">
        <el-empty description="暂无价格预警，添加一个吧！" />
      </div>
      
      <el-table v-else :data="alertStore.alerts" style="width: 100%">
        <el-table-column prop="symbol" label="币种" width="120" />
        <el-table-column label="预警类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getAlertTypeTag(row.type)">
              {{ getAlertTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标值" width="140">
          <template #default="{ row }">
            <span v-if="row.targetPrice !== undefined">
              ${{ row.targetPrice.toLocaleString() }}
            </span>
            <span v-else-if="row.targetChange !== undefined">
              {{ row.targetChange >= 0 ? '+' : '' }}{{ row.targetChange.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.triggeredAt" type="info">已触发</el-tag>
            <el-tag v-else :type="row.enabled ? 'success' : 'warning'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              size="small" 
              :type="row.enabled ? 'warning' : 'primary'"
              link
              @click="alertStore.toggleAlert(row.id)"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              link
              @click="deleteAlert(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加预警对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加价格预警"
      width="500px"
    >
      <el-form :model="newAlert" label-width="100px">
        <el-form-item label="币种">
          <el-select v-model="newAlert.symbol" placeholder="请选择币种">
            <el-option
              v-for="item in symbolOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="预警类型">
          <el-select v-model="newAlert.type" placeholder="请选择预警类型">
            <el-option label="价格高于" value="price_above" />
            <el-option label="价格低于" value="price_below" />
            <el-option label="24h涨幅超过" value="change_above" />
            <el-option label="24h跌幅超过" value="change_below" />
          </el-select>
        </el-form-item>
        
        <el-form-item 
          v-if="newAlert.type === 'price_above' || newAlert.type === 'price_below'" 
          label="目标价格"
        >
          <el-input-number 
            v-model="newAlert.targetPrice" 
            :min="0" 
            :precision="2"
            placeholder="请输入目标价格"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item 
          v-if="newAlert.type === 'change_above' || newAlert.type === 'change_below'" 
          label="目标涨跌幅"
        >
          <el-input-number 
            v-model="newAlert.targetChange" 
            :precision="2"
            placeholder="请输入目标涨跌幅（%）"
            style="width: 100%"
          />
          <span style="margin-left: 8px; color: #909399;">%</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addNewAlert" :disabled="!canAddAlert">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAlertStore } from '@/stores/alert'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { PriceAlert } from '@/stores/alert'
import { SYMBOLS } from '@/constants'

const alertStore = useAlertStore()
const showAddDialog = ref(false)
const symbolOptions = SYMBOLS

type AlertType = PriceAlert['type']

interface NewAlertForm {
  symbol: string
  type: AlertType
  targetPrice: number | undefined
  targetChange: number | undefined
  enabled: boolean
}

const newAlert = ref<NewAlertForm>({
  symbol: 'BTCUSDT',
  type: 'price_above',
  targetPrice: undefined as number | undefined,
  targetChange: undefined as number | undefined,
  enabled: true
})

const canAddAlert = computed(() => {
  if (!newAlert.value.symbol || !newAlert.value.type) return false
  if (
    (newAlert.value.type === 'price_above' || newAlert.value.type === 'price_below') &&
    newAlert.value.targetPrice === undefined
  ) return false
  if (
    (newAlert.value.type === 'change_above' || newAlert.value.type === 'change_below') &&
    newAlert.value.targetChange === undefined
  ) return false
  return true
})

const addNewAlert = () => {
  alertStore.addAlert({
    symbol: newAlert.value.symbol,
    type: newAlert.value.type,
    targetPrice: newAlert.value.targetPrice,
    targetChange: newAlert.value.targetChange,
    enabled: true
  })
  
  ElMessage.success('预警添加成功！')
  showAddDialog.value = false
  
  // 重置表单
  newAlert.value = {
    symbol: 'BTCUSDT',
    type: 'price_above',
    targetPrice: undefined,
    targetChange: undefined,
    enabled: true
  }
}

const deleteAlert = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个预警吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    alertStore.deleteAlert(id)
    ElMessage.success('删除成功！')
  } catch {
    // 用户取消
  }
}

const getAlertTypeName = (type: string): string => {
  const names: Record<string, string> = {
    price_above: '价格高于',
    price_below: '价格低于',
    change_above: '24h涨幅超过',
    change_below: '24h跌幅超过'
  }
  return names[type] || type
}

const getAlertTypeTag = (type: string): string => {
  const tags: Record<string, string> = {
    price_above: 'success',
    price_below: 'danger',
    change_above: 'warning',
    change_below: 'info'
  }
  return tags[type] || ''
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style scoped>
.alert {
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
</style>
