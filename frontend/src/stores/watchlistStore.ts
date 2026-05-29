/** 自选股 Store — 管理自选股列表 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WatchlistItem, WatchlistAdd } from '@/types/stock'
import { watchlistApi } from '@/services/api'

export const useWatchlistStore = defineStore('watchlist', () => {
  const items = ref<WatchlistItem[]>([])
  const loading = ref<boolean>(false)

  /** 加载自选股列表 */
  async function load() {
    loading.value = true
    try {
      const { data } = await watchlistApi.list()
      items.value = data
    } catch (e) {
      console.error('加载自选股失败:', e)
    } finally {
      loading.value = false
    }
  }

  /** 添加到自选股 */
  async function add(stock: WatchlistAdd) {
    try {
      const { data } = await watchlistApi.add(stock)
      items.value.unshift(data)
    } catch (e) {
      console.error('添加自选股失败:', e)
    }
  }

  /** 移除自选股 */
  async function remove(id: number) {
    try {
      await watchlistApi.remove(id)
      items.value = items.value.filter((i) => i.id !== id)
    } catch (e) {
      console.error('移除自选股失败:', e)
    }
  }

  /** 获取自选股代码列表（用于 WebSocket 订阅） */
  function getStockCodes(): string[] {
    return items.value.filter((i) => i.is_active).map((i) => i.stock_code)
  }

  return { items, loading, load, add, remove, getStockCodes }
})