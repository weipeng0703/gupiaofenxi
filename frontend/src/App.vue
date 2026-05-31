<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-left">
        <button v-if="isTablet" class="sidebar-toggle" @click="layoutStore.toggleWatchlist">☰</button>
        <h1 class="app-title">📈 股票分析助手</h1>
      </div>
      <nav v-if="isDesktop" class="header-nav">
        <RouterLink to="/" class="nav-link">首页</RouterLink>
        <RouterLink to="/rules" class="nav-link">📚 规则</RouterLink>
      </nav>
      <div class="header-right">
        <RouterLink v-if="!isDesktop" to="/rules" class="nav-link-mobile">📚</RouterLink>
        <button v-if="!isDesktop" class="signal-toggle" @click="layoutStore.toggleSignals">🔔</button>
        <span :class="['ws-status', wsStore.connected ? 'on' : 'off']">
          {{ wsStore.connected ? '● 已连接' : '○ 未连接' }}
        </span>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
    <!-- 手机端底部 Tab 导航 -->
    <nav v-if="isMobile" class="mobile-tabs">
      <button
        :class="['tab-btn', { active: layoutStore.activeTab === 'watchlist' }]"
        @click="layoutStore.setActiveTab('watchlist')"
      >
        📋 自选股
      </button>
      <button
        :class="['tab-btn', { active: layoutStore.activeTab === 'chart' }]"
        @click="layoutStore.setActiveTab('chart')"
      >
        📊 行情
      </button>
      <button
        :class="['tab-btn', { active: layoutStore.activeTab === 'signals' }]"
        @click="layoutStore.setActiveTab('signals')"
      >
        🔔 信号
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useWsStore } from '@/stores/wsStore'
import { useLayoutStore } from '@/stores/layoutStore'
import { useResponsive } from '@/composables/useResponsive'

const wsStore = useWsStore()
const layoutStore = useLayoutStore()
const { isMobile, isTablet, isDesktop } = useResponsive()
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-md);
  height: var(--header-height);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.sidebar-toggle,
.signal-toggle {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-md);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  transition: background 0.2s;
}

.sidebar-toggle:hover,
.signal-toggle:hover {
  background: var(--bg-hover);
}

.app-title {
  font-size: var(--font-size-md);
  margin: 0;
  color: var(--text-primary);
  white-space: nowrap;
}

.header-nav {
  display: flex;
  gap: var(--spacing-sm);
}

.nav-link {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--bg-hover);
  color: var(--stock-up);
}

.nav-link-mobile {
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.nav-link-mobile:hover {
  color: var(--stock-up);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.ws-status {
  color: var(--text-muted);
}

.ws-status.on {
  color: var(--stock-down);
}

.app-main {
  flex: 1;
  overflow: hidden;
}

/* ── 手机底部 Tab ── */

.mobile-tabs {
  display: flex;
  height: var(--mobile-tab-height);
  background: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
  flex-shrink: 0;
  z-index: 10;
}

.tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  padding: var(--spacing-sm) 0;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
}

.tab-btn.active {
  color: var(--stock-up);
  font-weight: bold;
}
</style>