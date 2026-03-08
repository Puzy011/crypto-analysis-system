<template>
  <div class="empty-state" :style="{ minHeight: height }">
    <el-icon :size="iconSize" :color="iconColor">
      <component :is="icon" />
    </el-icon>
    <p class="empty-title">{{ title }}</p>
    <p v-if="description" class="empty-description">{{ description }}</p>
    <slot name="action"></slot>
  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'

interface Props {
  icon?: any
  iconSize?: number
  iconColor?: string
  title?: string
  description?: string
  height?: string
}

withDefaults(defineProps<Props>(), {
  icon: Document,
  iconSize: 64,
  iconColor: '#C0C4CC',
  title: '暂无数据',
  description: '',
  height: '300px'
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.empty-title {
  margin: 0;
  color: #909399;
  font-size: 16px;
  font-weight: 500;
}

.empty-description {
  margin: 0;
  color: #C0C4CC;
  font-size: 14px;
}
</style>
