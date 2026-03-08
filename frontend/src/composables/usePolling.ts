/**
 * 轮询 Composable
 */
import { ref, onUnmounted } from 'vue'

interface UsePollingOptions {
  interval?: number
  immediate?: boolean
  onError?: (error: any) => void
}

export function usePolling(
  callback: () => Promise<void> | void,
  options: UsePollingOptions = {}
) {
  const {
    interval = 5000,
    immediate = true,
    onError
  } = options

  const isPolling = ref(false)
  const timer = ref<number | null>(null)

  const start = async () => {
    if (isPolling.value) return

    isPolling.value = true

    const poll = async () => {
      try {
        await callback()
      } catch (error) {
        console.error('Polling error:', error)
        onError?.(error)
      }

      if (isPolling.value) {
        timer.value = window.setTimeout(poll, interval)
      }
    }

    if (immediate) {
      await poll()
    } else {
      timer.value = window.setTimeout(poll, interval)
    }
  }

  const stop = () => {
    isPolling.value = false
    if (timer.value !== null) {
      clearTimeout(timer.value)
      timer.value = null
    }
  }

  const restart = async () => {
    stop()
    await start()
  }

  // 组件卸载时停止轮询
  onUnmounted(() => {
    stop()
  })

  return {
    isPolling,
    start,
    stop,
    restart
  }
}
