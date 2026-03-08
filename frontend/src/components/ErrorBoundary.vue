<template>
  <div v-if="hasError" class="error-boundary">
    <el-result
      icon="error"
      title="出错了"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="handleReset">
          <el-icon><Refresh /></el-icon>
          <span>重新加载</span>
        </el-button>
        <el-button @click="handleGoHome">
          <el-icon><HomeFilled /></el-icon>
          <span>返回首页</span>
        </el-button>
      </template>
    </el-result>
  </div>
  <slot v-else></slot>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()
const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((err: any) => {
  hasError.value = true
  errorMessage.value = err.message || '发生了未知错误'
  console.error('Error captured:', err)
  return false
})

const handleReset = () => {
  hasError.value = false
  errorMessage.value = ''
  window.location.reload()
}

const handleGoHome = () => {
  hasError.value = false
  errorMessage.value = ''
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}
</style>
