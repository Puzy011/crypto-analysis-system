<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <span>🚀 欢迎使用虚拟货币行情分析系统</span>
            </div>
          </template>
          <p>这是 MVP 版本，目前包含以下功能：</p>
          <ul>
            <li>✅ Binance 实时行情获取</li>
            <li>✅ K线图展示</li>
            <li>🔄 更多功能开发中...</li>
          </ul>
          <el-button type="primary" @click="$router.push('/market')">
            前往市场行情
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 系统状态</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="后端服务">
              <el-tag :type="backendHealth ? 'success' : 'danger'">
                {{ backendHealth ? '正常' : '异常' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最后检查">
              {{ lastCheckTime || '-' }}
            </el-descriptions-item>
          </el-descriptions>
          <el-button style="margin-top: 15px;" @click="checkHealth">
            检查后端状态
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const backendHealth = ref(false)
const lastCheckTime = ref('')

const checkHealth = async () => {
  try {
    const response = await axios.get('/api/health')
    backendHealth.value = response.data.status === 'healthy'
    lastCheckTime.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    backendHealth.value = false
    lastCheckTime.value = new Date().toLocaleString('zh-CN')
    console.error('Health check failed:', error)
  }
}

onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.welcome-card {
  text-align: center;
}

.welcome-card p {
  font-size: 16px;
  color: #606266;
}

.welcome-card ul {
  text-align: left;
  max-width: 400px;
  margin: 20px auto;
}

.welcome-card li {
  margin: 10px 0;
  font-size: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
