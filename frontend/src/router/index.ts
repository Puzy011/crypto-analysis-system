import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('@/views/Market.vue')
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('@/views/Watchlist.vue')
  },
  {
    path: '/alert',
    name: 'Alert',
    component: () => import('@/views/Alert.vue')
  },
  {
    path: '/prediction',
    name: 'Prediction',
    component: () => import('@/views/Prediction.vue')
  },
  {
    path: '/whale',
    name: 'Whale',
    component: () => import('@/views/Whale.vue')
  },
  {
    path: '/sentiment',
    name: 'Sentiment',
    component: () => import('@/views/Sentiment.vue')
  },
  {
    path: '/realtime-sentiment',
    name: 'RealtimeSentiment',
    component: () => import('@/views/RealtimeSentiment.vue')
  },
  {
    path: '/prediction-backtest',
    name: 'PredictionBacktest',
    component: () => import('@/views/PredictionBacktest.vue')
  },
  {
    path: '/realtime-prediction',
    name: 'RealtimePrediction',
    component: () => import('@/views/RealtimePrediction.vue')
  },
  {
    path: '/advanced-prediction',
    name: 'AdvancedPrediction',
    component: () => import('@/views/AdvancedPrediction.vue')
  },
  {
    path: '/enhanced-sentiment',
    name: 'EnhancedSentiment',
    component: () => import('@/views/EnhancedSentiment.vue')
  },
  {
    path: '/whale-analysis',
    name: 'WhaleAnalysis',
    component: () => import('@/views/WhaleAnalysis.vue')
  },
  {
    path: '/complete-ta',
    name: 'CompleteTA',
    component: () => import('@/views/CompleteTA.vue')
  },
  {
    path: '/enhanced-backtest',
    name: 'EnhancedBacktest',
    component: () => import('@/views/EnhancedBacktest.vue')
  },
  {
    path: '/comprehensive-sentiment',
    name: 'ComprehensiveSentiment',
    component: () => import('@/views/ComprehensiveSentiment.vue')
  },
  {
    path: '/topic-modeling',
    name: 'TopicModeling',
    component: () => import('@/views/TopicModeling.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
