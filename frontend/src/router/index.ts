import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置进度条
NProgress.configure({ showSpinner: false })

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('@/views/Market.vue'),
    meta: { title: '市场行情' }
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('@/views/Watchlist.vue'),
    meta: { title: '自选币' }
  },
  {
    path: '/alert',
    name: 'Alert',
    component: () => import('@/views/Alert.vue'),
    meta: { title: '价格预警' }
  },
  {
    path: '/prediction',
    name: 'Prediction',
    component: () => import('@/views/Prediction.vue'),
    meta: { title: 'AI预测' }
  },
  {
    path: '/whale',
    name: 'Whale',
    component: () => import('@/views/Whale.vue'),
    meta: { title: '庄家分析' }
  },
  {
    path: '/sentiment',
    name: 'Sentiment',
    component: () => import('@/views/Sentiment.vue'),
    meta: { title: '舆情分析' }
  },
  {
    path: '/realtime-sentiment',
    name: 'RealtimeSentiment',
    component: () => import('@/views/RealtimeSentiment.vue'),
    meta: { title: '实时舆情监控' }
  },
  {
    path: '/prediction-backtest',
    name: 'PredictionBacktest',
    component: () => import('@/views/PredictionBacktest.vue'),
    meta: { title: '预测回测验证' }
  },
  {
    path: '/realtime-prediction',
    name: 'RealtimePrediction',
    component: () => import('@/views/RealtimePrediction.vue'),
    meta: { title: '实时预测更新' }
  },
  {
    path: '/advanced-prediction',
    name: 'AdvancedPrediction',
    component: () => import('@/views/AdvancedPrediction.vue'),
    meta: { title: '高级预测模型' }
  },
  {
    path: '/enhanced-sentiment',
    name: 'EnhancedSentiment',
    component: () => import('@/views/EnhancedSentiment.vue'),
    meta: { title: '增强舆情分析' }
  },
  {
    path: '/whale-analysis',
    name: 'WhaleAnalysis',
    component: () => import('@/views/WhaleAnalysis.vue'),
    meta: { title: '巨鲸分析' }
  },
  {
    path: '/complete-ta',
    name: 'CompleteTA',
    component: () => import('@/views/CompleteTA.vue'),
    meta: { title: '完整技术指标' }
  },
  {
    path: '/enhanced-backtest',
    name: 'EnhancedBacktest',
    component: () => import('@/views/EnhancedBacktest.vue'),
    meta: { title: '增强回测系统' }
  },
  {
    path: '/comprehensive-sentiment',
    name: 'ComprehensiveSentiment',
    component: () => import('@/views/ComprehensiveSentiment.vue'),
    meta: { title: '综合舆情分析' }
  },
  {
    path: '/topic-modeling',
    name: 'TopicModeling',
    component: () => import('@/views/TopicModeling.vue'),
    meta: { title: '主题建模' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  NProgress.start()
  
  // 设置页面标题
  const title = to.meta.title as string
  document.title = title ? `${title} - 虚拟货币行情分析系统` : '虚拟货币行情分析系统'
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
