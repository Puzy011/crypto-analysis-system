import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface WatchItem {
  symbol: string
  name?: string
  addedAt: number
}

export const useWatchlistStore = defineStore('watchlist', () => {
  const watchlist = ref<WatchItem[]>([])
  const STORAGE_KEY = 'crypto-watchlist'

  // 从本地存储加载
  const loadFromStorage = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        watchlist.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load watchlist:', error)
    }
  }

  // 保存到本地存储
  const saveToStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist.value))
    } catch (error) {
      console.error('Failed to save watchlist:', error)
    }
  }

  // 添加自选
  const addToWatchlist = (symbol: string, name?: string) => {
    if (isInWatchlist(symbol)) {
      return false
    }
    watchlist.value.push({
      symbol,
      name,
      addedAt: Date.now()
    })
    saveToStorage()
    return true
  }

  // 从自选删除
  const removeFromWatchlist = (symbol: string) => {
    const index = watchlist.value.findIndex(item => item.symbol === symbol)
    if (index > -1) {
      watchlist.value.splice(index, 1)
      saveToStorage()
      return true
    }
    return false
  }

  // 检查是否在自选
  const isInWatchlist = (symbol: string): boolean => {
    return watchlist.value.some(item => item.symbol === symbol)
  }

  // 初始化
  loadFromStorage()

  // 监听变化自动保存
  watch(watchlist, () => {
    saveToStorage()
  }, { deep: true })

  return {
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist
  }
})
