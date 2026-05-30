<template>
  <div v-if="quote" class="stock-quote" :class="{ up: isUp, down: isDown }">
    <div class="stock-name">{{ quote.stock_name }}</div>
    <div class="stock-code">{{ quote.stock_code }}</div>
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
  padding: 12px 16px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #eee;
}

.stock-quote.up {
  border-color: #ef232a;
  background: rgba(239, 35, 42, 0.05);
}

.stock-quote.down {
  border-color: #14b143;
  background: rgba(20, 177, 67, 0.05);
}

.stock-name {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.stock-code {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.price-main {
  font-size: 28px;
  font-weight: bold;
  margin-top: 4px;
}

.stock-quote.up .price-main {
  color: #ef232a;
}

.stock-quote.down .price-main {
  color: #14b143;
}

.change-info {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 14px;
}

.stock-quote.up .change-info {
  color: #ef232a;
}

.stock-quote.down .change-info {
  color: #14b143;
}

.quote-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.detail-item {
  padding: 2px 0;
}

.empty {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>