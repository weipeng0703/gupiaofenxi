<template>
  <div class="stock-search">
    <input
      v-model="keyword"
      class="search-input"
      placeholder="输入股票代码或名称搜索..."
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
  // 输入时隐藏之前的搜索结果
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
  gap: 8px;
}

.search-input {
  width: 200px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-btn {
  padding: 6px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  background: #ef232a;
  color: #fff;
  border-color: #ef232a;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.result-item {
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: #f5f5f5;
}

.result-item .code {
  color: #ef232a;
  font-weight: bold;
  font-size: 14px;
}

.result-item .name {
  color: #333;
  font-size: 14px;
}
</style>