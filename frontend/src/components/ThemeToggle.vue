<template>
  <el-switch
    v-model="isDark"
    inline-prompt
    :active-icon="Moon"
    :inactive-icon="Sunny"
    @change="handleThemeChange"
    class="theme-toggle"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { Moon, Sunny } from '@element-plus/icons-vue'

const themeStore = useThemeStore()

const isDark = computed({
  get: () => themeStore.theme === 'dark',
  set: (value) => {
    themeStore.setTheme(value ? 'dark' : 'light')
  }
})

const handleThemeChange = () => {
  themeStore.toggleTheme()
}
</script>

<style scoped>
.theme-toggle {
  --el-switch-on-color: #2c3e50;
  --el-switch-off-color: #409eff;
}
</style>
