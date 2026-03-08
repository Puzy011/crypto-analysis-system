<template>
  <div class="loading-spinner" :style="{ minHeight: height }">
    <el-icon class="is-loading" :size="size" :color="color">
      <Loading />
    </el-icon>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

interface Props {
  size?: number
  color?: string
  text?: string
  height?: string
}

withDefaults(defineProps<Props>(), {
  size: 40,
  color: '#409EFF',
  text: '加载中...',
  height: '200px'
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.loading-text {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
</style>
