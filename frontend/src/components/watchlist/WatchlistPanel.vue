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
  border-right: 1px solid #eee;
  background: #fafafa;
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
  color: #333;
}

.watchlist-items {
  overflow-y: auto;
}

.watchlist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.watchlist-item:hover {
  background: #f0f0f0;
}

.watchlist-item.active {
  background: #e8e8e8;
  border-left: 3px solid #ef232a;
}

.item-main {
  display: flex;
  gap: 6px;
  flex: 1;
}

.item-name {
  font-size: 14px;
  color: #333;
  font-weight: bold;
}

.item-code {
  font-size: 12px;
  color: #999;
}

.item-quote {
  text-align: right;
}

.item-price {
  font-size: 14px;
  font-weight: bold;
}

.item-price.up { color: #ef232a }
.item-price.down { color: #14b143 }

.item-change {
  font-size: 12px;
}

.item-change.up { color: #ef232a }
.item-change.down { color: #14b143 }

.remove-btn {
  border: none;
  background: transparent;
  color: #ccc;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  margin-left: 8px;
}

.remove-btn:hover {
  color: #ef232a;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #999;
}

.empty {
  text-align: center;
  padding: 40px 16px;
  color: #999;
  font-size: 14px;
}
</style>