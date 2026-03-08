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
          :ellipsis="false"
          router
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          
          <el-menu-item index="/market">
            <el-icon><TrendCharts /></el-icon>
            <span>市场行情</span>
          </el-menu-item>
          
          <el-sub-menu index="prediction-menu">
            <template #title>
              <el-icon><MagicStick /></el-icon>
              <span>AI预测</span>
            </template>
            <el-menu-item index="/prediction">基础预测</el-menu-item>
            <el-menu-item index="/advanced-prediction">高级预测模型</el-menu-item>
            <el-menu-item index="/realtime-prediction">实时预测更新</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="whale-menu">
            <template #title>
              <el-icon><View /></el-icon>
              <span>庄家分析</span>
            </template>
            <el-menu-item index="/whale">基础庄家分析</el-menu-item>
            <el-menu-item index="/whale-analysis">巨鲸分析</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="sentiment-menu">
            <template #title>
              <el-icon><ChatLineSquare /></el-icon>
              <span>舆情分析</span>
            </template>
            <el-menu-item index="/sentiment">基础舆情</el-menu-item>
            <el-menu-item index="/enhanced-sentiment">增强舆情分析</el-menu-item>
            <el-menu-item index="/comprehensive-sentiment">综合舆情分析</el-menu-item>
            <el-menu-item index="/realtime-sentiment">实时舆情监控</el-menu-item>
            <el-menu-item index="/topic-modeling">主题建模</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="analysis-menu">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>技术分析</span>
            </template>
            <el-menu-item index="/complete-ta">完整技术指标</el-menu-item>
            <el-menu-item index="/prediction-backtest">预测回测验证</el-menu-item>
            <el-menu-item index="/enhanced-backtest">增强回测系统</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="tools-menu">
            <template #title>
              <el-icon><Grid /></el-icon>
              <span>工具</span>
            </template>
            <el-menu-item index="/watchlist">
              <el-icon><Star /></el-icon>
              <span>自选币</span>
            </el-menu-item>
            <el-menu-item index="/alert">
              <el-icon><Bell /></el-icon>
              <span>价格预警</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>
      <div class="header-right">
        <ThemeToggle />
        <el-tag type="success" style="margin-left: 12px;">增强版</el-tag>
      </div>
    </el-header>
    
    <!-- 主内容区 -->
    <el-main class="app-main">
      <router-view />
    </el-main>
    
    <!-- 底部导航（移动端） -->
    <el-footer class="app-footer mobile-only">
      <div class="mobile-nav">
        <div 
          class="nav-item" 
          :class="{ active: activeTab === '/' }"
          @click="handleTabChange('/')"
        >
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === '/market' }"
          @click="handleTabChange('/market')"
        >
          <el-icon><TrendCharts /></el-icon>
          <span>行情</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === '/watchlist' }"
          @click="handleTabChange('/watchlist')"
        >
          <el-icon><Star /></el-icon>
          <span>自选</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === '/prediction' }"
          @click="handleTabChange('/prediction')"
        >
          <el-icon><MagicStick /></el-icon>
          <span>预测</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === '/more' }"
          @click="handleTabChange('/more')"
        >
          <el-icon><Grid /></el-icon>
          <span>更多</span>
        </div>
      </div>
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
          <el-menu-item-group title="AI预测">
            <el-menu-item index="/prediction">
              <el-icon><MagicStick /></el-icon>
              <span>基础预测</span>
            </el-menu-item>
            <el-menu-item index="/advanced-prediction">
              <el-icon><MagicStick /></el-icon>
              <span>高级预测模型</span>
            </el-menu-item>
            <el-menu-item index="/realtime-prediction">
              <el-icon><Refresh /></el-icon>
              <span>实时预测更新</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <el-menu-item-group title="庄家分析">
            <el-menu-item index="/whale">
              <el-icon><View /></el-icon>
              <span>基础庄家分析</span>
            </el-menu-item>
            <el-menu-item index="/whale-analysis">
              <el-icon><View /></el-icon>
              <span>巨鲸分析</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <el-menu-item-group title="舆情分析">
            <el-menu-item index="/sentiment">
              <el-icon><ChatLineSquare /></el-icon>
              <span>基础舆情</span>
            </el-menu-item>
            <el-menu-item index="/enhanced-sentiment">
              <el-icon><ChatLineSquare /></el-icon>
              <span>增强舆情分析</span>
            </el-menu-item>
            <el-menu-item index="/comprehensive-sentiment">
              <el-icon><ChatLineSquare /></el-icon>
              <span>综合舆情分析</span>
            </el-menu-item>
            <el-menu-item index="/realtime-sentiment">
              <el-icon><DataLine /></el-icon>
              <span>实时舆情监控</span>
            </el-menu-item>
            <el-menu-item index="/topic-modeling">
              <el-icon><MagicStick /></el-icon>
              <span>主题建模</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <el-menu-item-group title="技术分析">
            <el-menu-item index="/complete-ta">
              <el-icon><TrendCharts /></el-icon>
              <span>完整技术指标</span>
            </el-menu-item>
            <el-menu-item index="/prediction-backtest">
              <el-icon><TrendCharts /></el-icon>
              <span>预测回测验证</span>
            </el-menu-item>
            <el-menu-item index="/enhanced-backtest">
              <el-icon><DataLine /></el-icon>
              <span>增强回测系统</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <el-menu-item-group title="工具">
            <el-menu-item index="/watchlist">
              <el-icon><Star /></el-icon>
              <span>自选币</span>
            </el-menu-item>
            <el-menu-item index="/alert">
              <el-icon><Bell /></el-icon>
              <span>价格预警</span>
            </el-menu-item>
          </el-menu-item-group>
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
import ThemeToggle from '@/components/ThemeToggle.vue'

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
  background: linear-gradient(to bottom, #f5f7fa 0%, #e8eef5 100%);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 0 20px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
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
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.header-left .el-icon {
  color: #ffffff !important;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-center :deep(.el-menu) {
  border-bottom: none;
  flex: 1;
  background: transparent;
}

.header-center :deep(.el-menu-item),
.header-center :deep(.el-sub-menu__title) {
  padding: 0 15px;
  color: rgba(255, 255, 255, 0.9);
  border-bottom: 3px solid transparent;
}

.header-center :deep(.el-menu-item:hover),
.header-center :deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #ffffff;
}

.header-center :deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: #ffffff;
  border-bottom-color: #ffffff;
}

.header-center :deep(.el-menu-item .el-icon),
.header-center :deep(.el-sub-menu__title .el-icon) {
  margin-right: 5px;
  color: rgba(255, 255, 255, 0.9);
}

.header-center :deep(.el-sub-menu__icon-arrow) {
  color: rgba(255, 255, 255, 0.9);
}

.header-right {
  min-width: 100px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.header-right .el-tag {
  font-weight: 600;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

.mobile-nav {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: space-around;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 100%;
  cursor: pointer;
  transition: all 0.3s;
  color: #909399;
}

.nav-item:active {
  background-color: #f5f7fa;
}

.nav-item.active {
  color: #409EFF;
}

.nav-item .el-icon {
  font-size: 22px;
}

.nav-item span {
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

.more-menu :deep(.el-menu-item-group__title) {
  padding: 12px 20px 8px;
  font-size: 13px;
  color: #909399;
  font-weight: 600;
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
