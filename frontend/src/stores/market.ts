/**
 * 市场数据状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { marketApi } from '@/api'

export interface MarketData {
  symbol: string
  price: number
  change24h: number
  volume24h: number
  high24h: number
  low24h: number
  timestamp: number
}

export const useMarketStore = defineStore('market', () => {
  const marketData = ref<MarketData[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<number>(0)

  const fetchMarketData = async (symbols?: string[]) => {
    loading.value = true
    error.value = null

    try {
      const response = await marketApi.getMarketData(symbols)
      marketData.value = response.data || []
      lastUpdate.value = Date.now()
    } catch (err: any) {
      error.value = err.message || '获取市场数据失败'
      console.error('Failed to fetch market data:', err)
    } finally {
      loading.value = false
    }
  }

  const getSymbolData = (symbol: string) => {
    return marketData.value.find(item => item.symbol === symbol)
  }

  const clearError = () => {
    error.value = null
  }

  return {
    marketData,
    loading,
    error,
    lastUpdate,
    fetchMarketData,
    getSymbolData,
    clearError
  }
})
