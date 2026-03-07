import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface PriceAlert {
  id: string
  symbol: string
  type: 'price_above' | 'price_below' | 'change_above' | 'change_below'
  targetPrice?: number
  targetChange?: number
  enabled: boolean
  createdAt: number
  triggeredAt?: number
}

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<PriceAlert[]>([])
  const STORAGE_KEY = 'crypto-alerts'

  // 生成唯一ID
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  // 从本地存储加载
  const loadFromStorage = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        alerts.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load alerts:', error)
    }
  }

  // 保存到本地存储
  const saveToStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts.value))
    } catch (error) {
      console.error('Failed to save alerts:', error)
    }
  }

  // 添加预警
  const addAlert = (alert: Omit<PriceAlert, 'id' | 'createdAt'>): PriceAlert => {
    const newAlert: PriceAlert = {
      ...alert,
      id: generateId(),
      createdAt: Date.now()
    }
    alerts.value.push(newAlert)
    saveToStorage()
    return newAlert
  }

  // 更新预警
  const updateAlert = (id: string, updates: Partial<PriceAlert>) => {
    const index = alerts.value.findIndex(a => a.id === id)
    if (index > -1) {
      alerts.value[index] = { ...alerts.value[index], ...updates }
      saveToStorage()
      return true
    }
    return false
  }

  // 删除预警
  const deleteAlert = (id: string): boolean => {
    const index = alerts.value.findIndex(a => a.id === id)
    if (index > -1) {
      alerts.value.splice(index, 1)
      saveToStorage()
      return true
    }
    return false
  }

  // 检查预警是否触发
  const checkAlert = (alert: PriceAlert, currentPrice: number, priceChange24h: number): boolean => {
    if (!alert.enabled) return false
    if (alert.triggeredAt) return false

    switch (alert.type) {
      case 'price_above':
        if (alert.targetPrice && currentPrice >= alert.targetPrice) {
          return true
        }
        break
      case 'price_below':
        if (alert.targetPrice && currentPrice <= alert.targetPrice) {
          return true
        }
        break
      case 'change_above':
        if (alert.targetChange && priceChange24h >= alert.targetChange) {
          return true
        }
        break
      case 'change_below':
        if (alert.targetChange && priceChange24h <= alert.targetChange) {
          return true
        }
        break
    }
    return false
  }

  // 标记预警已触发
  const markAsTriggered = (id: string) => {
    updateAlert(id, { triggeredAt: Date.now() })
  }

  // 启用/禁用预警
  const toggleAlert = (id: string) => {
    const alert = alerts.value.find(a => a.id === id)
    if (alert) {
      updateAlert(id, { enabled: !alert.enabled })
    }
  }

  // 初始化
  loadFromStorage()

  // 监听变化自动保存
  watch(alerts, () => {
    saveToStorage()
  }, { deep: true })

  return {
    alerts,
    addAlert,
    updateAlert,
    deleteAlert,
    checkAlert,
    markAsTriggered,
    toggleAlert
  }
})
