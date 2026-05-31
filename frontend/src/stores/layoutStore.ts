import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLayoutStore = defineStore('layout', () => {
  /** 手机端底部 Tab 当前激活面板 */
  const activeTab = ref<'chart' | 'watchlist' | 'signals'>('chart')

  /** 平板端侧栏 overlay 开关 */
  const watchlistOpen = ref(false)
  const signalsOpen = ref(false)

  function setActiveTab(tab: 'chart' | 'watchlist' | 'signals') {
    activeTab.value = tab
  }

  function toggleWatchlist() {
    watchlistOpen.value = !watchlistOpen.value
    signalsOpen.value = false
  }

  function toggleSignals() {
    signalsOpen.value = !signalsOpen.value
    watchlistOpen.value = false
  }

  function closeOverlays() {
    watchlistOpen.value = false
    signalsOpen.value = false
  }

  return {
    activeTab,
    watchlistOpen,
    signalsOpen,
    setActiveTab,
    toggleWatchlist,
    toggleSignals,
    closeOverlays,
  }
})