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
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.period-group {
  display: flex;
  gap: 4px;
}

.period-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.period-btn:hover {
  background: #f5f5f5;
}

.period-btn.active {
  background: #ef232a;
  color: #fff;
  border-color: #ef232a;
}

.action-group {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f0f0f0;
}
</style>