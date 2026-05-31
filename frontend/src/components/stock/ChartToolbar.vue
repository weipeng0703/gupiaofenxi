<template>
  <div class="chart-toolbar">
    <div class="period-group">
      <button
        v-for="opt in PERIOD_OPTIONS"
        :key="opt.value"
        :class="['period-btn', { active: currentPeriod === opt.value }]"
        @click="switchPeriod(opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>
    <div class="action-group">
      <button class="action-btn" @click="$emit('refresh')" title="刷新数据">🔄</button>
      <button class="action-btn" @click="$emit('fullscreen')" title="全屏">⛶</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PERIOD_OPTIONS } from '@/services/chartConfig'

const props = defineProps<{
  currentPeriod: string
}>()

const emit = defineEmits<{
  (e: 'switchPeriod', period: string): void
  (e: 'refresh'): void
  (e: 'fullscreen'): void
}>()

function switchPeriod(period: string) {
  emit('switchPeriod', period)
}
</script>

<style scoped>
.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-primary);
}

.period-group {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.period-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: all 0.2s;
}

.period-btn:hover {
  background: var(--bg-hover);
}

.period-btn.active {
  background: var(--stock-up);
  color: var(--bg-primary);
  border-color: var(--stock-up);
}

.action-group {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--font-size-md);
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--bg-hover);
}

@media (max-width: 480px) {
  .period-btn {
    padding: 2px 6px;
    font-size: var(--font-size-xs);
  }
}
</style>