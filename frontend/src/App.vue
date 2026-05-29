<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-left">
        <h1 class="app-title">📈 股票分析助手</h1>
      </div>
      <nav class="header-nav">
        <RouterLink to="/" class="nav-link">首页</RouterLink>
      </nav>
      <div class="header-right">
        <span :class="['ws-status', wsStore.connected ? 'on' : 'off']">
          {{ wsStore.connected ? '● 已连接' : '○ 未连接' }}
        </span>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useWsStore } from '@/stores/wsStore'

const wsStore = useWsStore()
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.app-title {
  font-size: 18px;
  margin: 0;
  color: #333;
}

.header-nav {
  display: flex;
  gap: 12px;
}

.nav-link {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f5f5f5;
  color: #ef232a;
}

.header-right {
  font-size: 12px;
}

.ws-status {
  color: #999;
}

.ws-status.on {
  color: #14b143;
}

.app-main {
  flex: 1;
  overflow: hidden;
}
</style>