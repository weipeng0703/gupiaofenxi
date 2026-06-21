/** 自选股 Store — 管理自选股列表 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WatchlistItem, WatchlistAdd } from '@/types/stock'
import { watchlistApi } from '@/services/api'

export const useWatchlistStore = defineStore('watchlist', () => {
  const items = ref<WatchlistItem[]>([])
  const loading = ref<boolean>(false)

  /** 特别关注股票列表 */
  const specialWatchItems = computed(() => items.value.filter((i) => i.is_special_watch))

  /** 特别关注股票代码列表 */
  const specialWatchCodes = computed(() => specialWatchItems.value.map((i) => i.stock_code))

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

  /** 切换特别关注状态 */
  async function toggleSpecialWatch(id: number, value: boolean) {
    try {
      const { data } = await watchlistApi.update(id, { is_special_watch: value })
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx >= 0) {
        items.value[idx] = data
      }
    } catch (e) {
      console.error('切换特别关注失败:', e)
    }
  }

  /** 获取自选股代码列表（用于 WebSocket 订阅） */
  function getStockCodes(): string[] {
    return items.value.filter((i) => i.is_active).map((i) => i.stock_code)
  }

  return { items, loading, specialWatchItems, specialWatchCodes, load, add, remove, toggleSpecialWatch, getStockCodes }
})