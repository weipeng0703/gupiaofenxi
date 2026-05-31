<template>
  <div class="watchlist-panel">
    <div class="panel-header">
      <h3>自选股</h3>
      <StockSearch @select="onAddStock" />
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="items.length" class="watchlist-items">
      <div
        v-for="item in items"
        :key="item.id"
        :class="['watchlist-item', { active: currentCode === item.stock_code }]"
        @click="onSelectStock(item)"
      >
        <div class="item-main">
          <span class="item-name">{{ item.stock_name }}</span>
          <span class="item-code">{{ item.stock_code }}</span>
        </div>
        <div v-if="getQuote(item.stock_code)" class="item-quote">
          <span :class="['item-price', getQuote(item.stock_code)!.change_pct > 0 ? 'up' : 'down']">
            {{ formatPrice(getQuote(item.stock_code)!.price) }}
          </span>
          <span :class="['item-change', getQuote(item.stock_code)!.change_pct > 0 ? 'up' : 'down']">
            {{ formatChange(getQuote(item.stock_code)!.change_pct) }}
          </span>
        </div>
        <button class="remove-btn" @click.stop="onRemove(item.id)">✕</button>
      </div>
    </div>

    <div v-else class="empty">暂无自选股，请搜索添加</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WatchlistItem, StockSearchResult } from '@/types/stock'
import { useWatchlistStore } from '@/stores/watchlistStore'
import { useStockStore } from '@/stores/stockStore'
import { formatPrice, formatChange } from '@/utils/colorUtils'
import StockSearch from '@/components/stock/StockSearch.vue'

const watchlistStore = useWatchlistStore()
const stockStore = useStockStore()

const items = computed(() => watchlistStore.items)
const loading = computed(() => watchlistStore.loading)
const currentCode = computed(() => stockStore.currentCode)

function getQuote(code: string) {
  return stockStore.getQuote(code)
}

async function onAddStock(stock: StockSearchResult) {
  await watchlistStore.add({
    stock_code: stock.stock_code,
    stock_name: stock.stock_name,
    market: stock.market,
  })
  // 自动选中新添加的股票
  stockStore.loadStock(stock.stock_code)
}

function onSelectStock(item: WatchlistItem) {
  stockStore.loadStock(item.stock_code)
}

async function onRemove(id: number) {
  await watchlistStore.remove(id)
}
</script>

<style scoped>
.watchlist-panel {
  padding: 0;
  background: var(--bg-sidebar);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-primary);
}

.panel-header h3 {
  font-size: var(--font-size-md);
  margin: 0;
  color: var(--text-primary);
  white-space: nowrap;
}

.watchlist-items {
  overflow-y: auto;
  flex: 1;
}

.watchlist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px var(--spacing-md);
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border-light);
}

.watchlist-item:hover {
  background: var(--bg-hover);
}

.watchlist-item.active {
  background: var(--bg-active);
  border-left: 3px solid var(--stock-up);
}

.item-main {
  display: flex;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-weight: bold;
}

.item-code {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.item-quote {
  text-align: right;
  flex-shrink: 0;
}

.item-price {
  font-size: var(--font-size-base);
  font-weight: bold;
  font-family: var(--font-mono);
}

.item-price.up { color: var(--text-up) }
.item-price.down { color: var(--text-down) }

.item-change {
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
}

.item-change.up { color: var(--text-up) }
.item-change.down { color: var(--text-down) }

.remove-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: 2px 6px;
  margin-left: var(--spacing-sm);
  border-radius: var(--radius-sm);
  transition: color 0.2s;
}

.remove-btn:hover {
  color: var(--stock-up);
}

.loading {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--text-muted);
}

.empty {
  text-align: center;
  padding: var(--spacing-xl) var(--spacing-md);
  color: var(--text-muted);
  font-size: var(--font-size-base);
}
</style>