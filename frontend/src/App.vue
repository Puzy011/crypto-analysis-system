<template>
  <el-container class="app-container">
    <!-- 顶部导航（PC端） -->
    <el-header class="app-header desktop-only">
      <div class="header-left">
        <el-icon :size="30" color="#409EFF">
          <TrendCharts />
        </el-icon>
        <h1>虚拟货币行情分析系统</h1>
      </div>
      <div class="header-center">
        <el-menu
          :default-active="$route.path"
          mode="horizontal"
          :ellipsis="true"
          router
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/market">市场行情</el-menu-item>
          <el-menu-item index="/watchlist">
            <el-icon><Star /></el-icon>
            <span>自选币</span>
          </el-menu-item>
          <el-menu-item index="/alert">
            <el-icon><Bell /></el-icon>
            <span>价格预警</span>
          </el-menu-item>
          <el-menu-item index="/prediction">
            <el-icon><MagicStick /></el-icon>
            <span>AI预测</span>
          </el-menu-item>
          <el-menu-item index="/whale">
            <el-icon><View /></el-icon>
            <span>庄家分析</span>
          </el-menu-item>
          <el-menu-item index="/sentiment">
            <el-icon><ChatLineSquare /></el-icon>
            <span>舆情分析</span>
          </el-menu-item>
          <el-sub-menu title="高级功能">
            <el-menu-item index="/advanced-prediction">
              <el-icon><MagicStick /></el-icon>
              <span>高级预测模型</span>
            </el-menu-item>
            <el-menu-item index="/enhanced-sentiment">
              <el-icon><ChatLineSquare /></el-icon>
              <span>增强舆情分析</span>
            </el-menu-item>
            <el-menu-item index="/whale-analysis">
              <el-icon><View /></el-icon>
              <span>巨鲸分析</span>
            </el-menu-item>
            <el-menu-item index="/realtime-sentiment">
              <el-icon><DataLine /></el-icon>
              <span>实时舆情监控</span>
            </el-menu-item>
            <el-menu-item index="/prediction-backtest">
              <el-icon><TrendCharts /></el-icon>
              <span>预测回测验证</span>
            </el-menu-item>
            <el-menu-item index="/realtime-prediction">
              <el-icon><Refresh /></el-icon>
              <span>实时预测更新</span>
            </el-menu-item>
            <el-menu-item index="/complete-ta">
              <el-icon><TrendCharts /></el-icon>
              <span>完整技术指标</span>
            </el-menu-item>
            <el-menu-item index="/enhanced-backtest">
              <el-icon><DataLine /></el-icon>
              <span>增强回测系统</span>
            </el-menu-item>
            <el-menu-item index="/comprehensive-sentiment">
              <el-icon><ChatLineSquare /></el-icon>
              <span>综合舆情分析</span>
            </el-menu-item>
            <el-menu-item index="/topic-modeling">
              <el-icon><MagicStick /></el-icon>
              <span>主题建模</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>
      <div class="header-right">
        <el-tag type="success">增强版</el-tag>
      </div>
    </el-header>
    
    <!-- 主内容区 -->
    <el-main class="app-main">
      <router-view />
    </el-main>
    
    <!-- 底部导航（移动端） -->
    <el-footer class="app-footer mobile-only">
      <el-tab-bar v-model="activeTab" @change="handleTabChange">
        <el-tab-bar-item name="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-tab-bar-item>
        <el-tab-bar-item name="/market">
          <el-icon><TrendCharts /></el-icon>
          <span>行情</span>
        </el-tab-bar-item>
        <el-tab-bar-item name="/watchlist">
          <el-icon><Star /></el-icon>
          <span>自选</span>
        </el-tab-bar-item>
        <el-tab-bar-item name="/prediction">
          <el-icon><MagicStick /></el-icon>
          <span>预测</span>
        </el-tab-bar-item>
        <el-tab-bar-item name="/more">
          <el-icon><Grid /></el-icon>
          <span>更多</span>
        </el-tab-bar-item>
      </el-tab-bar>
    </el-footer>
    
    <!-- 更多功能弹窗（移动端） -->
    <el-drawer
      v-model="moreDrawerVisible"
      title="更多功能"
      direction="btt"
      size="60%"
      class="mobile-only"
    >
      <div class="more-menu">
        <el-menu
          :default-active="$route.path"
          @select="handleMoreMenuSelect"
        >
          <el-menu-item index="/alert">
            <el-icon><Bell /></el-icon>
            <span>价格预警</span>
          </el-menu-item>
          <el-menu-item index="/whale">
            <el-icon><View /></el-icon>
            <span>庄家分析</span>
          </el-menu-item>
          <el-menu-item index="/sentiment">
            <el-icon><ChatLineSquare /></el-icon>
            <span>舆情分析</span>
          </el-menu-item>
          <el-menu-item index="/advanced-prediction">
            <el-icon><MagicStick /></el-icon>
            <span>高级预测模型</span>
          </el-menu-item>
          <el-menu-item index="/enhanced-sentiment">
            <el-icon><ChatLineSquare /></el-icon>
            <span>增强舆情分析</span>
          </el-menu-item>
          <el-menu-item index="/whale-analysis">
            <el-icon><View /></el-icon>
            <span>巨鲸分析</span>
          </el-menu-item>
          <el-menu-item index="/realtime-sentiment">
            <el-icon><DataLine /></el-icon>
            <span>实时舆情监控</span>
          </el-menu-item>
          <el-menu-item index="/prediction-backtest">
            <el-icon><TrendCharts /></el-icon>
            <span>预测回测验证</span>
          </el-menu-item>
          <el-menu-item index="/realtime-prediction">
            <el-icon><Refresh /></el-icon>
            <span>实时预测更新</span>
          </el-menu-item>
          <el-menu-item index="/complete-ta">
            <el-icon><TrendCharts /></el-icon>
            <span>完整技术指标</span>
          </el-menu-item>
          <el-menu-item index="/enhanced-backtest">
            <el-icon><DataLine /></el-icon>
            <span>增强回测系统</span>
          </el-menu-item>
          <el-menu-item index="/comprehensive-sentiment">
            <el-icon><ChatLineSquare /></el-icon>
            <span>综合舆情分析</span>
          </el-menu-item>
          <el-menu-item index="/topic-modeling">
            <el-icon><MagicStick /></el-icon>
            <span>主题建模</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-drawer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  TrendCharts, Star, Bell, MagicStick, View, ChatLineSquare, 
  DataLine, Refresh, HomeFilled, Grid 
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('/')
const moreDrawerVisible = ref(false)

watch(() => route.path, (newPath) => {
  if (['/', '/market', '/watchlist', '/prediction'].includes(newPath)) {
    activeTab.value = newPath
  } else {
    activeTab.value = '/more'
  }
}, { immediate: true })

const handleTabChange = (tabName: string) => {
  if (tabName === '/more') {
    moreDrawerVisible.value = true
  } else {
    router.push(tabName)
  }
}

const handleMoreMenuSelect = (index: string) => {
  moreDrawerVisible.value = false
  router.push(index)
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 280px;
}

.header-left h1 {
  font-size: 20px;
  margin: 0;
  color: #303133;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-center :deep(.el-menu) {
  border-bottom: none;
}

.app-main {
  flex: 1;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}

.app-footer {
  flex-shrink: 0;
  padding: 0;
  background-color: #fff;
  border-top: 1px solid #e4e7ed;
  height: 60px;
}

.app-footer :deep(.el-tab-bar) {
  height: 100%;
  border: none;
}

.app-footer :deep(.el-tab-bar-item) {
  flex-direction: column;
  gap: 2px;
  height: 100%;
  padding: 6px 0;
}

.app-footer :deep(.el-tab-bar-item .el-icon) {
  font-size: 22px;
}

.app-footer :deep(.el-tab-bar-item span) {
  font-size: 12px;
}

.desktop-only {
  display: flex;
}

.mobile-only {
  display: none;
}

.more-menu {
  padding: 10px 0;
}

.more-menu :deep(.el-menu) {
  border: none;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }
  
  .mobile-only {
    display: block !important;
  }
  
  .app-main {
    padding: 10px;
  }
}

@media (min-width: 769px) {
  .app-main {
    padding: 20px;
  }
}
</style>
