<template>
  <div v-if="quote" class="stock-quote" :class="{ up: isUp, down: isDown }">
    <div class="quote-header">
      <div class="stock-name">{{ quote.stock_name }}</div>
      <div class="stock-code">{{ quote.stock_code }}</div>
    </div>
    <div class="price-main">{{ formatPrice(quote.price) }}</div>
    <div class="change-info">
      <span class="change-pct">{{ formatChange(quote.change_pct) }}</span>
      <span class="change-amt">{{ quote.change_amt > 0 ? '+' : '' }}{{ quote.change_amt.toFixed(2) }}</span>
    </div>
    <div class="quote-details">
      <div class="detail-item">开: {{ formatPrice(quote.open) }}</div>
      <div class="detail-item">高: {{ formatPrice(quote.high) }}</div>
      <div class="detail-item">低: {{ formatPrice(quote.low) }}</div>
      <div class="detail-item">昨收: {{ formatPrice(quote.prev_close) }}</div>
      <div class="detail-item">量: {{ formatVolume(quote.volume) }}</div>
      <div class="detail-item">额: {{ formatVolume(quote.amount) }}</div>
    </div>
  </div>
  <div v-else class="stock-quote empty">暂无行情数据</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RealtimeQuote } from '@/types/stock'
import { formatPrice, formatChange, formatVolume } from '@/utils/colorUtils'

const props = defineProps<{
  quote: RealtimeQuote | null | undefined
}>()

const isUp = computed(() => props.quote?.change_pct != null && props.quote.change_pct > 0)
const isDown = computed(() => props.quote?.change_pct != null && props.quote.change_pct < 0)
</script>

<style scoped>
.stock-quote {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
}

.stock-quote.up {
  border-color: var(--stock-up);
  background: var(--bg-up-tint);
}

.stock-quote.down {
  border-color: var(--stock-down);
  background: var(--bg-down-tint);
}

.quote-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.stock-name {
  font-size: var(--font-size-md);
  font-weight: bold;
  color: var(--text-primary);
}

.stock-code {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.price-main {
  font-size: var(--font-size-xl);
  font-weight: bold;
  margin-top: var(--spacing-xs);
  font-family: var(--font-mono);
}

.stock-quote.up .price-main {
  color: var(--text-up);
}

.stock-quote.down .price-main {
  color: var(--text-down);
}

.change-info {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-base);
  font-family: var(--font-mono);
}

.stock-quote.up .change-info {
  color: var(--text-up);
}

.stock-quote.down .change-info {
  color: var(--text-down);
}

.quote-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.detail-item {
  padding: 2px 0;
}

@media (max-width: 768px) {
  .quote-details {
    grid-template-columns: repeat(2, 1fr);
  }
}

.empty {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-lg);
}
</style>