/** 股票数据 Store — 管理 K 线数据、指标和当前选中的股票 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StockFullResponse, RealtimeQuote } from '@/types/stock'
import { stocksApi } from '@/services/api'

export const useStockStore = defineStore('stock', () => {
  // 当前股票完整数据
  const currentStock = ref<StockFullResponse | null>(null)
  // 当前选中股票代码
  const currentCode = ref<string>('')
  // 当前周期
  const currentPeriod = ref<string>('daily')
  // 实时行情映射
  const realtimeQuotes = ref<Map<string, RealtimeQuote>>(new Map())
  // 加载状态
  const loading = ref<boolean>(false)
  // 错误信息
  const error = ref<string>('')

  /** 加载股票完整数据 */
  async function loadStock(code: string, period: string = 'daily', startDate?: string, endDate?: string) {
    loading.value = true
    error.value = ''
    currentCode.value = code
    currentPeriod.value = period

    try {
      const { data } = await stocksApi.getFull(code, period, startDate, endDate)
      currentStock.value = data
    } catch (e: any) {
      error.value = e.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  /** 更新实时行情（来自 WebSocket 推送） */
  function updateQuotes(quotes: RealtimeQuote[]) {
    for (const q of quotes) {
      realtimeQuotes.value.set(q.stock_code, q)
    }
  }

  /** 获取指定股票的实时行情 */
  function getQuote(code: string): RealtimeQuote | undefined {
    return realtimeQuotes.value.get(code)
  }

  /** 清空数据 */
  function clear() {
    currentStock.value = null
    currentCode.value = ''
    error.value = ''
  }

  return {
    currentStock,
    currentCode,
    currentPeriod,
    realtimeQuotes,
    loading,
    error,
    loadStock,
    updateQuotes,
    getQuote,
    clear,
  }
})