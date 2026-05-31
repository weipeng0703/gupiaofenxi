<template>
  <div class="home-view">
    <!-- ── Desktop: 三栏布局 ── -->
    <template v-if="isDesktop">
      <aside class="sidebar-left">
        <WatchlistPanel />
      </aside>
      <main class="main-area">
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
      </main>
      <aside class="sidebar-right">
        <SignalPanel />
      </aside>
    </template>

    <!-- ── Tablet: 主区域 + Overlay 侧栏 ── -->
    <template v-if="isTablet">
      <main class="main-area main-area--full">
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
      </main>
      <!-- Overlay backdrop -->
      <div
        v-if="layoutStore.watchlistOpen || layoutStore.signalsOpen"
        class="overlay-backdrop"
        @click="layoutStore.closeOverlays"
      ></div>
      <!-- Overlay 侧栏 -->
      <aside v-if="layoutStore.watchlistOpen" class="sidebar-overlay sidebar-overlay--left">
        <WatchlistPanel />
      </aside>
      <aside v-if="layoutStore.signalsOpen" class="sidebar-overlay sidebar-overlay--right">
        <SignalPanel />
      </aside>
    </template>

    <!-- ── Mobile: 单面板 Tab 切换 ── -->
    <template v-if="isMobile">
      <div v-if="layoutStore.activeTab === 'watchlist'" class="mobile-panel">
        <WatchlistPanel />
      </div>
      <div v-if="layoutStore.activeTab === 'chart'" class="mobile-panel">
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
          />
        </div>
        <div v-else class="welcome">
          <h2>股票分析助手</h2>
          <p>请在自选股 Tab 搜索并添加自选股</p>
          <div class="connection-status">
            <span :class="['status-dot', wsStore.connected ? 'on' : 'off']"></span>
            {{ wsStore.connected ? '已连接' : '未连接' }}
          </div>
        </div>
      </div>
      <div v-if="layoutStore.activeTab === 'signals'" class="mobile-panel">
        <SignalPanel />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useStockStore } from '@/stores/stockStore'
import { useWatchlistStore } from '@/stores/watchlistStore'
import { useSignalStore } from '@/stores/signalStore'
import { useWsStore } from '@/stores/wsStore'
import { useLayoutStore } from '@/stores/layoutStore'
import { useResponsive } from '@/composables/useResponsive'
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
const layoutStore = useLayoutStore()
const { isMobile, isTablet, isDesktop } = useResponsive()

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
  height: calc(100vh - var(--header-height));
  overflow: hidden;
}

/* ── Desktop 三栏 ── */

.sidebar-left {
  width: var(--sidebar-left-width);
  flex-shrink: 0;
  border-right: 1px solid var(--border-primary);
  background: var(--bg-sidebar);
}

.sidebar-right {
  width: var(--sidebar-right-width);
  flex-shrink: 0;
  border-left: 1px solid var(--border-primary);
  background: var(--bg-sidebar);
}

.main-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  background: var(--bg-primary);
}

.main-area--full {
  flex: 1;
  width: 100%;
}

.stock-main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-height: 0;
}

/* ── Tablet Overlay ── */

.overlay-backdrop {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  z-index: 40;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  bottom: 0;
  width: 300px;
  background: var(--bg-sidebar);
  z-index: 50;
  box-shadow: var(--shadow-lg);
  overflow-y: auto;
}

.sidebar-overlay--left {
  left: 0;
  animation: slideInLeft 0.3s ease;
}

.sidebar-overlay--right {
  right: 0;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@keyframes slideInRight {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

/* ── Mobile 单面板 ── */

.mobile-panel {
  flex: 1;
  overflow-y: auto;
  height: calc(100vh - var(--header-height) - var(--mobile-tab-height));
}

/* ── Welcome ── */

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.welcome h2 {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.welcome p {
  font-size: var(--font-size-base);
}

.connection-status {
  margin-top: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.on {
  background: var(--stock-down);
}

.status-dot.off {
  background: var(--text-muted);
}

.last-msg {
  color: var(--text-muted);
}
</style>