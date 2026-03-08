<template>
  <div class="skeleton-loader">
    <el-skeleton :rows="rows" :animated="animated" :loading="loading">
      <template #template>
        <slot name="template">
          <el-skeleton-item 
            v-for="i in rows" 
            :key="i" 
            variant="text" 
            style="margin-bottom: 16px;"
          />
        </slot>
      </template>
      <template #default>
        <slot></slot>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading?: boolean
  rows?: number
  animated?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: true,
  rows: 5,
  animated: true
})
</script>

<style scoped>
.skeleton-loader {
  width: 100%;
}
</style>
