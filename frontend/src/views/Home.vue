<template>
  <div class="home">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-banner" shadow="never">
      <div class="banner-content">
        <div class="banner-left">
          <h1>
            <el-icon class="banner-icon"><TrendCharts /></el-icon>
            虚拟货币行情分析系统
          </h1>
          <p class="banner-subtitle">基于 AI 的智能加密货币分析平台</p>
          <div class="banner-tags">
            <el-tag type="success" effect="dark">实时行情</el-tag>
            <el-tag type="warning" effect="dark">AI 预测</el-tag>
            <el-tag type="danger" effect="dark">庄家分析</el-tag>
            <el-tag type="info" effect="dark">舆情监控</el-tag>
          </div>
        </div>
        <div class="banner-right">
          <el-statistic title="系统状态" :value="backendHealth ? '运行中' : '离线'">
            <template #suffix>
              <el-icon :color="backendHealth ? '#67C23A' : '#F56C6C'">
                <CircleCheck v-if="backendHealth" />
                <CircleClose v-else />
              </el-icon>
            </template>
          </el-statistic>
        </div>
      </div>
    </el-card>

    <!-- 快速导航 -->
    <el-row :gutter="20" class="quick-nav">
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/market')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#409EFF"><TrendCharts /></el-icon>
            <div class="nav-text">
              <div class="nav-title">市场行情</div>
              <div class="nav-desc">实时K线</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/prediction')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#67C23A"><MagicStick /></el-icon>
            <div class="nav-text">
              <div class="nav-title">AI 预测</div>
              <div class="nav-desc">智能分析</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/whale')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#E6A23C"><View /></el-icon>
            <div class="nav-text">
              <div class="nav-title">庄家分析</div>
              <div class="nav-desc">大单监控</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/sentiment')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#F56C6C"><ChatLineSquare /></el-icon>
            <div class="nav-text">
              <div class="nav-title">舆情分析</div>
              <div class="nav-desc">情感监控</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/watchlist')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#909399"><Star /></el-icon>
            <div class="nav-text">
              <div class="nav-title">自选币</div>
              <div class="nav-desc">收藏管理</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="6" :lg="4">
        <el-card class="nav-card" shadow="hover" @click="$router.push('/alert')">
          <div class="nav-card-content">
            <el-icon class="nav-icon" color="#409EFF"><Bell /></el-icon>
            <div class="nav-text">
              <div class="nav-title">价格预警</div>
              <div class="nav-desc">智能提醒</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能特性 -->
    <el-row :gutter="20" class="features">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon color="#409EFF"><DataAnalysis /></el-icon>
              <span>多模型 AI 预测</span>
            </div>
          </template>
          <ul class="feature-list">
            <li>XGBoost 梯度提升</li>
            <li>LightGBM 轻量模型</li>
            <li>Prophet 时间序列</li>
            <li>Random Forest 随机森林</li>
            <li>集成学习预测</li>
          </ul>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon color="#67C23A"><Monitor /></el-icon>
              <span>实时监控系统</span>
            </div>
          </template>
          <ul class="feature-list">
            <li>实时价格更新</li>
            <li>大单实时监控</li>
            <li>舆情实时分析</li>
            <li>预测动态更新</li>
            <li>多时间框架分析</li>
          </ul>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon color="#E6A23C"><PieChart /></el-icon>
              <span>专业技术分析</span>
            </div>
          </template>
          <ul class="feature-list">
            <li>完整技术指标库</li>
            <li>多周期K线分析</li>
            <li>回测验证系统</li>
            <li>策略性能评估</li>
            <li>风险收益分析</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-row :gutter="20" class="system-info">
      <el-col :xs="24" :sm="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>系统状态</span>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="后端服务">
              <el-tag :type="backendHealth ? 'success' : 'danger'" size="small">
                {{ backendHealth ? '正常运行' : '连接失败' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="API 版本">
              <el-tag type="info" size="small">v2.0.0</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最后检查">
              {{ lastCheckTime || '未检查' }}
            </el-descriptions-item>
          </el-descriptions>
          <el-button 
            type="primary" 
            :loading="checking"
            @click="checkHealth"
            style="margin-top: 15px; width: 100%;"
          >
            <el-icon><Refresh /></el-icon>
            <span>刷新状态</span>
          </el-button>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>快速开始</span>
            </div>
          </template>
          <div class="quick-start">
            <el-steps direction="vertical" :active="1">
              <el-step title="查看市场行情" description="实时监控加密货币价格走势" />
              <el-step title="添加自选币" description="收藏关注的交易对" />
              <el-step title="设置价格预警" description="及时获取价格变动通知" />
              <el-step title="使用 AI 预测" description="获取智能分析和预测结果" />
            </el-steps>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { 
  TrendCharts, MagicStick, View, ChatLineSquare, Star, Bell,
  CircleCheck, CircleClose, DataAnalysis, Monitor, PieChart,
  Setting, InfoFilled, Refresh
} from '@element-plus/icons-vue'

const router = useRouter()
const backendHealth = ref(false)
const lastCheckTime = ref('')
const checking = ref(false)

const checkHealth = async () => {
  checking.value = true
  try {
    const response = await axios.get('/api/health')
    backendHealth.value = response.data.status === 'healthy'
    lastCheckTime.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    backendHealth.value = false
    lastCheckTime.value = new Date().toLocaleString('zh-CN')
    console.error('Health check failed:', error)
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
}

/* 欢迎横幅 */
.welcome-banner {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.welcome-banner :deep(.el-card__body) {
  padding: 40px;
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.banner-left h1 {
  font-size: 32px;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.banner-icon {
  font-size: 36px;
}

.banner-subtitle {
  font-size: 16px;
  margin: 0 0 20px 0;
  opacity: 0.9;
}

.banner-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.banner-right :deep(.el-statistic__head) {
  color: rgba(255, 255, 255, 0.8);
}

.banner-right :deep(.el-statistic__content) {
  color: white;
  font-size: 24px;
}

/* 快速导航 */
.quick-nav {
  margin-bottom: 24px;
}

.nav-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.nav-card:hover {
  transform: translateY(-4px);
}

.nav-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-icon {
  font-size: 36px;
}

.nav-text {
  flex: 1;
}

.nav-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.nav-desc {
  font-size: 13px;
  color: #909399;
}

/* 功能特性 */
.features {
  margin-bottom: 24px;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.feature-header .el-icon {
  font-size: 20px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  padding: 8px 0;
  color: #606266;
  position: relative;
  padding-left: 20px;
}

.feature-list li:before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #67C23A;
  font-weight: bold;
}

/* 系统信息 */
.system-info {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.quick-start {
  padding: 10px 0;
}

.quick-start :deep(.el-step__title) {
  font-size: 14px;
}

.quick-start :deep(.el-step__description) {
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .welcome-banner :deep(.el-card__body) {
    padding: 24px;
  }
  
  .banner-content {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  
  .banner-left h1 {
    font-size: 24px;
    justify-content: center;
  }
  
  .banner-subtitle {
    font-size: 14px;
  }
  
  .banner-tags {
    justify-content: center;
  }
  
  .nav-card {
    margin-bottom: 12px;
  }
  
  .features .el-col,
  .system-info .el-col {
    margin-bottom: 20px;
  }
}
</style>
