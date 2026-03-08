/**
 * WebSocket 连接 Composable
 */
import { ref, onUnmounted } from 'vue'

interface UseWebSocketOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
  reconnect?: boolean
  reconnectInterval?: number
  reconnectAttempts?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    reconnectInterval = 3000,
    reconnectAttempts = 5
  } = options

  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectCount = ref(0)

  const connect = () => {
    try {
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        isConnected.value = true
        reconnectCount.value = 0
        onOpen?.()
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (error) {
          console.error('WebSocket message parse error:', error)
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }

      ws.value.onclose = () => {
        isConnected.value = false
        onClose?.()

        // 自动重连
        if (reconnect && reconnectCount.value < reconnectAttempts) {
          reconnectCount.value++
          console.log(`WebSocket reconnecting... (${reconnectCount.value}/${reconnectAttempts})`)
          setTimeout(connect, reconnectInterval)
        }
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
    }
  }

  const send = (data: any) => {
    if (ws.value && isConnected.value) {
      ws.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  const close = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  // 组件卸载时关闭连接
  onUnmounted(() => {
    close()
  })

  return {
    ws,
    isConnected,
    connect,
    send,
    close
  }
}
