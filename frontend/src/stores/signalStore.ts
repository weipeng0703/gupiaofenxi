/** 信号 Store — 管理买卖信号通知 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SignalItem } from '@/types/stock'
import { signalsApi } from '@/services/api'

export const useSignalStore = defineStore('signal', () => {
  const signals = ref<SignalItem[]>([])
  const loading = ref<boolean>(false)

  /** 未读信号数量 */
  const unreadCount = computed(() => signals.value.filter((s) => !s.is_read).length)

  /** 加载信号列表 */
  async function load(limit: number = 50) {
    loading.value = true
    try {
      const { data } = await signalsApi.list({ limit })
      signals.value = data
    } catch (e) {
      console.error('加载信号失败:', e)
    } finally {
      loading.value = false
    }
  }

  /** 添加新信号（来自 WebSocket 推送） */
  function addSignal(signal: SignalItem) {
    // 避免重复
    const exists = signals.value.find((s) => s.id === signal.id)
    if (!exists) {
      signals.value.unshift(signal)
    }
  }

  /** 标记信号为已读 */
  async function markRead(id: number) {
    try {
      await signalsApi.markRead(id)
      const signal = signals.value.find((s) => s.id === id)
      if (signal) signal.is_read = true
    } catch (e) {
      console.error('标记已读失败:', e)
    }
  }

  /** 获取指定股票的信号 */
  function getByStock(code: string): SignalItem[] {
    return signals.value.filter((s) => s.stock_code === code)
  }

  return { signals, loading, unreadCount, load, addSignal, markRead, getByStock }
})