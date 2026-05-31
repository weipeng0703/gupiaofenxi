<template>
  <div class="signal-panel">
    <div class="panel-header">
      <h3>信号通知</h3>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </div>

    <div v-if="signals.length" class="signal-list">
      <div
        v-for="signal in signals"
        :key="signal.id"
        :class="['signal-item', signal.signal_type, { unread: !signal.is_read }]"
        @click="onMarkRead(signal)"
      >
        <div class="signal-icon">
          {{ signal.signal_type === 'BUY' ? '↑' : '↓' }}
        </div>
        <div class="signal-content">
          <div class="signal-title">
            <span :class="['signal-type', signal.signal_type]">
              {{ signal.signal_type === 'BUY' ? '买入' : '卖出' }}
            </span>
            <span class="signal-stock">{{ signal.stock_code }}</span>
          </div>
          <div class="signal-strategy">{{ signal.strategy_name }}</div>
          <div class="signal-detail">
            价格: {{ signal.price.toFixed(2) }} | 置信度: {{ (signal.confidence * 100).toFixed(0) }}%
          </div>
          <div class="signal-time">{{ signal.timestamp }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty">暂无信号</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SignalItem } from '@/types/stock'
import { useSignalStore } from '@/stores/signalStore'

const props = defineProps<{
  stockCode?: string
}>()

const signalStore = useSignalStore()

const signals = computed(() => {
  if (props.stockCode) return signalStore.getByStock(props.stockCode)
  return signalStore.signals.slice(0, 20)
})

const unreadCount = computed(() => {
  if (props.stockCode) return signalStore.getByStock(props.stockCode).filter(s => !s.is_read).length
  return signalStore.unreadCount
})

async function onMarkRead(signal: SignalItem) {
  if (!signal.is_read) {
    await signalStore.markRead(signal.id)
  }
}
</script>

<style scoped>
.signal-panel {
  background: var(--bg-sidebar);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-primary);
}

.panel-header h3 {
  font-size: var(--font-size-md);
  margin: 0;
  color: var(--text-primary);
}

.badge {
  background: var(--stock-up);
  color: var(--bg-primary);
  border-radius: 10px;
  padding: 2px 8px;
  font-size: var(--font-size-sm);
  font-weight: bold;
}

.signal-list {
  overflow-y: auto;
  flex: 1;
}

.signal-item {
  display: flex;
  gap: 10px;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
  transition: background 0.2s;
}

.signal-item:hover {
  background: var(--bg-hover);
}

.signal-item.unread {
  background: var(--bg-up-tint);
}

.signal-icon {
  font-size: var(--font-size-lg);
  width: 30px;
  text-align: center;
  font-weight: bold;
}

.signal-item.BUY .signal-icon {
  color: var(--stock-up);
}

.signal-item.SELL .signal-icon {
  color: var(--stock-down);
}

.signal-content {
  flex: 1;
  min-width: 0;
}

.signal-title {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-size-base);
}

.signal-type.BUY {
  color: var(--text-up);
  font-weight: bold;
}

.signal-type.SELL {
  color: var(--text-down);
  font-weight: bold;
}

.signal-stock {
  color: var(--text-primary);
  font-weight: bold;
}

.signal-strategy {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-top: 2px;
}

.signal-detail {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin-top: 2px;
  font-family: var(--font-mono);
}

.signal-time {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: 2px;
}

.empty {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-muted);
}
</style>