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
  background: #fafafa;
  border-left: 1px solid #eee;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  font-size: 16px;
  margin: 0;
}

.badge {
  background: #ef232a;
  color: #fff;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: bold;
}

.signal-list {
  overflow-y: auto;
}

.signal-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.signal-item:hover {
  background: #f0f0f0;
}

.signal-item.unread {
  background: #fff9f0;
}

.signal-icon {
  font-size: 20px;
  width: 30px;
  text-align: center;
}

.signal-item.BUY .signal-icon {
  color: #ef232a;
}

.signal-item.SELL .signal-icon {
  color: #14b143;
}

.signal-content {
  flex: 1;
}

.signal-title {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.signal-type.BUY {
  color: #ef232a;
  font-weight: bold;
}

.signal-type.SELL {
  color: #14b143;
  font-weight: bold;
}

.signal-stock {
  color: #333;
  font-weight: bold;
}

.signal-strategy {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.signal-detail {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.signal-time {
  font-size: 11px;
  color: #bbb;
  margin-top: 2px;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>