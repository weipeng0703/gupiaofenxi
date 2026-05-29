<template>
  <div class="home-view">
    <div class="sidebar-left">
      <WatchlistPanel />
    </div>
    <div class="main-area">
      <div v-if="stockStore.currentStock" class="stock-main">
        <StockQuote :quote="stockStore.getQuote(stockStore.currentCode)" />
        <ChartToolbar
          :current-period="stockStore.currentPeriod"
          @switch-period="onSwitchPeriod"
          @refresh="onRefresh"
        />
        <KlineChart
          :kline="stockStore.currentStock.kline"
          :indicators="stockStore.currentStock.indicators"
          :signals="stockStore.currentStock.signals"
          height="600px"
        />
      </div>
      <div v-else class="welcome">
        <h2>股票分析助手</h2>
        <p>请在左侧搜索并添加自选股，或选择已有的自选股开始分析</p>
        <div class="connection-status">
          <span :class="['status-dot', wsStore.connected ? 'on' : 'off']"></span>
          {{ wsStore.connected ? '已连接' : '未连接' }}
          <span v-if="wsStore.lastMessageTime" class="last-msg">最后更新: {{ wsStore.lastMessageTime }}</span>
        </div>
      </div>
    </div>
    <div class="sidebar-right">
      <SignalPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useStockStore } from '@/stores/stockStore'
import { useWatchlistStore } from '@/stores/watchlistStore'
import { useSignalStore } from '@/stores/signalStore'
import { useWsStore } from '@/stores/wsStore'
import { wsManager } from '@/services/websocket'
import WatchlistPanel from '@/components/watchlist/WatchlistPanel.vue'
import SignalPanel from '@/components/signal/SignalPanel.vue'
import KlineChart from '@/components/stock/KlineChart.vue'
import ChartToolbar from '@/components/stock/ChartToolbar.vue'
import StockQuote from '@/components/stock/StockQuote.vue'

const stockStore = useStockStore()
const watchlistStore = useWatchlistStore()
const signalStore = useSignalStore()
const wsStore = useWsStore()

onMounted(async () => {
  await watchlistStore.load()
  await signalStore.load()

  // 连接 WebSocket
  wsManager.connect()
  wsManager.on('connected', () => wsStore.setConnected(true))
  wsManager.on('disconnected', () => wsStore.setReconnecting())

  wsManager.on('quote_update', (msg) => {
    wsStore.updateLastMessage()
    const quotes = msg.payload.quotes as any[]
    stockStore.updateQuotes(quotes)
  })

  wsManager.on('signal_alert', (msg) => {
    const signal = msg.payload.signal as any
    signalStore.addSignal(signal)
  })

  // 订阅自选股行情
  const codes = watchlistStore.getStockCodes()
  if (codes.length) {
    wsManager.subscribe(codes)
  }
})

onUnmounted(() => {
  wsManager.disconnect()
})

function onSwitchPeriod(period: string) {
  stockStore.loadStock(stockStore.currentCode, period)
}

function onRefresh() {
  stockStore.loadStock(stockStore.currentCode, stockStore.currentPeriod)
}
</script>

<style scoped>
.home-view {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar-left {
  width: 280px;
  flex-shrink: 0;
}

.main-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.sidebar-right {
  width: 240px;
  flex-shrink: 0;
}

.stock-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.welcome h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 8px;
}

.welcome p {
  font-size: 14px;
}

.connection-status {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.on {
  background: #14b143;
}

.status-dot.off {
  background: #999;
}

.last-msg {
  color: #999;
}
</style>