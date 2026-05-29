/** WebSocket 连接状态 Store */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWsStore = defineStore('ws', () => {
  const connected = ref<boolean>(false)
  const reconnecting = ref<boolean>(false)
  const lastMessageTime = ref<string>('')

  function setConnected(val: boolean) {
    connected.value = val
    reconnecting.value = false
  }

  function setReconnecting() {
    connected.value = false
    reconnecting.value = true
  }

  function updateLastMessage() {
    lastMessageTime.value = new Date().toLocaleTimeString()
  }

  return { connected, reconnecting, lastMessageTime, setConnected, setReconnecting, updateLastMessage }
})