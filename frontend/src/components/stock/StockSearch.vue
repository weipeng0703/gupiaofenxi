<template>
  <div class="stock-search">
    <input
      v-model="keyword"
      class="search-input"
      placeholder="输入股票代码或名称..."
      @input="onInput"
      @keydown.enter="doSearch"
    />
    <button class="search-btn" @click="doSearch">搜索</button>

    <!-- 搜索结果下拉 -->
    <div v-if="results.length && showResults" class="search-results">
      <div
        v-for="item in results"
        :key="item.stock_code"
        class="result-item"
        @click="selectStock(item)"
      >
        <span class="code">{{ item.stock_code }}</span>
        <span class="name">{{ item.stock_name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { StockSearchResult } from '@/types/stock'
import { stocksApi } from '@/services/api'

const emit = defineEmits<{
  (e: 'select', stock: StockSearchResult): void
}>()

const keyword = ref('')
const results = ref<StockSearchResult[]>([])
const showResults = ref(true)

async function doSearch() {
  if (!keyword.value.trim()) return
  try {
    const { data } = await stocksApi.search(keyword.value.trim())
    results.value = data
    showResults.value = true
  } catch (e) {
    console.error('搜索失败:', e)
  }
}

function onInput() {
  showResults.value = false
}

function selectStock(stock: StockSearchResult) {
  emit('select', stock)
  keyword.value = stock.stock_name
  showResults.value = false
  results.value = []
}
</script>

<style scoped>
.stock-search {
  position: relative;
  display: flex;
  gap: var(--spacing-sm);
  flex: 1;
  min-width: 0;
}

.search-input {
  flex: 1;
  min-width: 0;
  max-width: 200px;
  padding: 6px var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.search-input:focus {
  outline: none;
  border-color: var(--border-focus);
}

.search-btn {
  padding: 6px var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-btn:hover {
  background: var(--stock-up);
  color: var(--bg-primary);
  border-color: var(--stock-up);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: var(--shadow-md);
}

.result-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: var(--bg-hover);
}

.result-item .code {
  color: var(--stock-up);
  font-weight: bold;
  font-size: var(--font-size-base);
  font-family: var(--font-mono);
}

.result-item .name {
  color: var(--text-primary);
  font-size: var(--font-size-base);
}
</style>