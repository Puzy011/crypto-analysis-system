/**
 * 主题状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type Theme = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>((localStorage.getItem('app-theme') as Theme) || 'light')

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('app-theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  // 初始化主题
  document.documentElement.setAttribute('data-theme', theme.value)

  return {
    theme,
    setTheme,
    toggleTheme
  }
})
