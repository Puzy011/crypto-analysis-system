/**
 * 主题切换 Composable
 */
import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

const THEME_KEY = 'app-theme'

export function useTheme() {
  const theme = ref<Theme>((localStorage.getItem(THEME_KEY) as Theme) || 'light')

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
  }

  // 监听主题变化，更新 DOM 和 localStorage
  watch(theme, (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem(THEME_KEY, newTheme)
  }, { immediate: true })

  return {
    theme,
    toggleTheme,
    setTheme
  }
}
