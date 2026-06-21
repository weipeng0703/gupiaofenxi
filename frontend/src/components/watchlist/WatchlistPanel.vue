<template>
  <div class="watchlist-panel">
    <!-- 搜索框 -->
    <div class="panel-header">
      <h3>📋 自选股</h3>
      <StockSearch @select="onSearchSelect" />
    </div>

    <!-- 搜索结果分组选择弹窗 -->
    <div v-if="searchResult && showGroupPicker" class="group-picker-overlay" @click.self="showGroupPicker = false">
      <div class="group-picker">
        <div class="picker-title">将 {{ searchResult.stock_name }} 添加到：</div>
        <button class="picker-btn picker-btn--special" @click="addToSpecialWatch">
          ★ 特别关注
        </button>
        <button class="picker-btn picker-btn--watchlist" @click="addToWatchlist">
          📋 自选股
        </button>
        <button
          v-for="g in groupStore.groups"
          :key="g.id"
          class="picker-btn"
          @click="addToGroup(g.id)"
        >
          <span class="color-dot" :style="{ background: g.color }"></span>
          {{ g.name }}
        </button>
        <button class="picker-btn picker-btn--new" @click="showNewGroupFromSearch = true">
          ✚ 新建分组
        </button>
        <button class="picker-close" @click="showGroupPicker = false">取消</button>
      </div>
    </div>

    <!-- 特别关注分区 -->
    <div v-if="watchlistStore.specialWatchItems.length" class="section special-watch-section">
      <div class="section-header section-header--special" @click="collapsedSpecial = !collapsedSpecial">
        <button class="collapse-btn">{{ collapsedSpecial ? '▸' : '▾' }}</button>
        <span class="section-title">★ 特别关注</span>
        <span class="section-count">{{ watchlistStore.specialWatchItems.length }}</span>
      </div>
      <div v-if="!collapsedSpecial" class="watchlist-items">
        <div
          v-for="item in watchlistStore.specialWatchItems"
          :key="'sw-' + item.id"
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
          <button class="star-btn star-btn--active" @click.stop="onToggleSpecialWatch(item.id, false)" title="取消特别关注">★</button>
        </div>
      </div>
    </div>

    <!-- 自选股列表 -->
    <div class="section">
      <div class="section-header" @click="collapsedWatchlist = !collapsedWatchlist">
        <button class="collapse-btn">{{ collapsedWatchlist ? '▸' : '▾' }}</button>
        <span class="section-title">自选股</span>
        <span class="section-count">{{ watchlistStore.items.length }}</span>
      </div>
      <div v-if="collapsedWatchlist"></div>
      <div v-else-if="watchlistStore.loading" class="loading">加载中...</div>
      <div v-else-if="watchlistStore.items.length" class="watchlist-items">
        <div
          v-for="item in watchlistStore.items"
          :key="item.id"
          :class="['watchlist-item', { active: currentCode === item.stock_code }]"
          @click="onSelectStock(item)"
        >
          <div class="item-main">
            <span class="item-name">{{ item.stock_name }}</span>
            <span class="item-code">{{ item.stock_code }}</span>
            <span v-if="groupStore.isInAnyGroup(item.stock_code).length" class="item-group-badges">
              <span
                v-for="gid in groupStore.isInAnyGroup(item.stock_code)"
                :key="gid"
                class="group-badge"
                :style="{ background: getGroupColor(gid) }"
              ></span>
            </span>
          </div>
          <div v-if="getQuote(item.stock_code)" class="item-quote">
            <span :class="['item-price', getQuote(item.stock_code)!.change_pct > 0 ? 'up' : 'down']">
              {{ formatPrice(getQuote(item.stock_code)!.price) }}
            </span>
            <span :class="['item-change', getQuote(item.stock_code)!.change_pct > 0 ? 'up' : 'down']">
              {{ formatChange(getQuote(item.stock_code)!.change_pct) }}
            </span>
          </div>
          <button
            :class="['star-btn', { 'star-btn--active': item.is_special_watch }]"
            @click.stop="onToggleSpecialWatch(item.id, !item.is_special_watch)"
            :title="item.is_special_watch ? '取消特别关注' : '加入特别关注'"
          >{{ item.is_special_watch ? '★' : '☆' }}</button>
          <button class="remove-btn" @click.stop="onRemoveFromWatchlist(item.id)">✕</button>
        </div>
      </div>
      <div v-else class="empty">暂无自选股，请搜索添加</div>
    </div>

    <!-- 各分组 -->
    <div v-for="g in groupStore.groups" :key="g.id" class="section group-section">
      <div class="section-header" :style="{ borderLeftColor: g.color }" @click="toggleCollapse(g.id)">
        <button class="collapse-btn">
          {{ collapsed[g.id] ? '▸' : '▾' }}
        </button>
        <span class="color-dot" :style="{ background: g.color }"></span>
        <span class="section-title">{{ g.name }}</span>
        <span class="section-count">{{ groupStore.getMembers(g.id).length }}</span>
        <div class="group-actions">
          <button class="group-action-btn" @click="startEditGroup(g)" title="编辑">✎</button>
          <button class="group-action-btn group-action-btn--danger" @click="onDeleteGroup(g.id)" title="删除">✕</button>
        </div>
      </div>

      <!-- 编辑分组弹窗 -->
      <div v-if="editingGroup && editingGroup.id === g.id" class="group-edit-inline">
        <input v-model="editingGroup.name" class="edit-input" placeholder="分组名称" />
        <div class="color-picker-row">
          <button
            v-for="c in GROUP_COLORS"
            :key="c"
            :class="['color-pick', { active: editingGroup.color === c }]"
            :style="{ background: c }"
            @click="editingGroup.color = c"
          ></button>
        </div>
        <button class="edit-save-btn" @click="saveEditGroup">保存</button>
        <button class="edit-cancel-btn" @click="editingGroup = null">取消</button>
      </div>

      <!-- 分组成员列表 -->
      <div v-if="!collapsed[g.id]" class="group-members">
        <div
          v-for="member in groupStore.getMembers(g.id)"
          :key="member.stock_code"
          :class="['watchlist-item', { active: currentCode === member.stock_code }]"
          @click="onSelectGroupMember(member)"
        >
          <div class="item-main">
            <span class="item-name">{{ member.stock_name }}</span>
            <span class="item-code">{{ member.stock_code }}</span>
          </div>
          <div v-if="getQuote(member.stock_code)" class="item-quote">
            <span :class="['item-price', getQuote(member.stock_code)!.change_pct > 0 ? 'up' : 'down']">
              {{ formatPrice(getQuote(member.stock_code)!.price) }}
            </span>
            <span :class="['item-change', getQuote(member.stock_code)!.change_pct > 0 ? 'up' : 'down']">
              {{ formatChange(getQuote(member.stock_code)!.change_pct) }}
            </span>
          </div>
          <div class="move-btns">
            <button class="move-btn" @click.stop="onMoveMember(g.id, member.stock_code, 'up')" title="上移">↑</button>
            <button class="move-btn" @click.stop="onMoveMember(g.id, member.stock_code, 'down')" title="下移">↓</button>
          </div>
          <button class="remove-btn" @click.stop="onRemoveFromGroup(g.id, member.stock_code)">✕</button>
        </div>
      </div>
    </div>

    <!-- 新建分组按钮 -->
    <div class="create-group-bar">
      <button v-if="!showNewGroup" class="create-group-btn" @click="showNewGroup = true">
        ✚ 新建分组
      </button>
      <div v-if="showNewGroup" class="create-group-form">
        <input v-model="newGroupName" class="edit-input" placeholder="分组名称" />
        <div class="color-picker-row">
          <button
            v-for="c in GROUP_COLORS"
            :key="c"
            :class="['color-pick', { active: newGroupColor === c }]"
            :style="{ background: c }"
            @click="newGroupColor = c"
          ></button>
        </div>
        <button class="edit-save-btn" @click="onCreateGroup">创建</button>
        <button class="edit-cancel-btn" @click="showNewGroup = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { WatchlistItem, StockSearchResult, StockGroup } from '@/types/stock'
import { GROUP_COLORS } from '@/types/stock'
import { useWatchlistStore } from '@/stores/watchlistStore'
import { useGroupStore } from '@/stores/groupStore'
import { useStockStore } from '@/stores/stockStore'
import { formatPrice, formatChange } from '@/utils/colorUtils'
import StockSearch from '@/components/stock/StockSearch.vue'

const watchlistStore = useWatchlistStore()
const groupStore = useGroupStore()
const stockStore = useStockStore()

const currentCode = ref(stockStore.currentCode)
const collapsed = reactive<Record<number, boolean>>({})
const collapsedSpecial = ref(false)
const collapsedWatchlist = ref(false)

// 新建分组状态
const showNewGroup = ref(false)
const newGroupName = ref('')
const newGroupColor = ref(GROUP_COLORS[0])

// 搜索后分组选择状态
const searchResult = ref<StockSearchResult | null>(null)
const showGroupPicker = ref(false)
const showNewGroupFromSearch = ref(false)

// 编辑分组状态
const editingGroup = ref<StockGroup | null>(null)

onMounted(async () => {
  await groupStore.loadGroups()
})

function getQuote(code: string) {
  return stockStore.getQuote(code)
}

function getGroupColor(groupId: number): string {
  const g = groupStore.groups.find(g => g.id === groupId)
  return g?.color || '#5470c6'
}

function toggleCollapse(groupId: number) {
  collapsed[groupId] = !collapsed[groupId]
}

// ── 搜索选择 ──

function onSearchSelect(stock: StockSearchResult) {
  searchResult.value = stock
  showGroupPicker.value = true
}

async function addToWatchlist() {
  if (!searchResult.value) return
  await watchlistStore.add({
    stock_code: searchResult.value.stock_code,
    stock_name: searchResult.value.stock_name,
    market: searchResult.value.market,
  })
  showGroupPicker.value = false
  searchResult.value = null
}

async function addToSpecialWatch() {
  if (!searchResult.value) return
  const existing = watchlistStore.items.find(
    i => i.stock_code === searchResult.value!.stock_code
  )
  if (!existing) {
    await watchlistStore.add({
      stock_code: searchResult.value.stock_code,
      stock_name: searchResult.value.stock_name,
      market: searchResult.value.market,
    })
  }
  // Find the item (just added or existing) and mark as special watch
  const item = watchlistStore.items.find(i => i.stock_code === searchResult.value!.stock_code)
  if (item && !item.is_special_watch) {
    await watchlistStore.toggleSpecialWatch(item.id, true)
  }
  showGroupPicker.value = false
  searchResult.value = null
}

async function addToGroup(groupId: number) {
  if (!searchResult.value) return
  // 先确保在自选股中
  const existing = watchlistStore.items.find(
    i => i.stock_code === searchResult.value!.stock_code
  )
  if (!existing) {
    await watchlistStore.add({
      stock_code: searchResult.value.stock_code,
      stock_name: searchResult.value.stock_name,
      market: searchResult.value.market,
    })
  }
  // 再添加到分组
  try {
    await groupStore.addMember(
      groupId,
      searchResult.value.stock_code,
      searchResult.value.stock_name,
      searchResult.value.market,
    )
  } catch (e: any) {
    alert(e?.response?.data?.detail || '添加到分组失败')
  }
  showGroupPicker.value = false
  searchResult.value = null
}

// ── 自选股操作 ──

function onSelectStock(item: WatchlistItem) {
  stockStore.loadStock(item.stock_code)
}

async function onRemoveFromWatchlist(id: number) {
  await watchlistStore.remove(id)
}

async function onToggleSpecialWatch(id: number, value: boolean) {
  await watchlistStore.toggleSpecialWatch(id, value)
}

// ── 分组操作 ──

function onSelectGroupMember(member: { stock_code: string }) {
  stockStore.loadStock(member.stock_code)
}

async function onDeleteGroup(groupId: number) {
  const g = groupStore.groups.find(g => g.id === groupId)
  if (!g) return
  if (!confirm(`确认删除分组「${g.name}」？分组内的标的不会从自选股中移除。`)) return
  await groupStore.deleteGroup(groupId)
}

function startEditGroup(g: StockGroup) {
  editingGroup.value = { ...g }
}

async function saveEditGroup() {
  if (!editingGroup.value) return
  await groupStore.updateGroup(editingGroup.value.id, {
    name: editingGroup.value.name,
    color: editingGroup.value.color,
  })
  editingGroup.value = null
}

async function onMoveMember(groupId: number, stockCode: string, direction: 'up' | 'down') {
  await groupStore.moveMember(groupId, stockCode, direction)
}

async function onRemoveFromGroup(groupId: number, stockCode: string) {
  await groupStore.removeMember(groupId, stockCode)
}

async function onCreateGroup() {
  if (!newGroupName.value.trim()) return
  await groupStore.createGroup({
    name: newGroupName.value.trim(),
    color: newGroupColor.value || GROUP_COLORS[0],
  })
  showNewGroup.value = false
  newGroupName.value = ''
  newGroupColor.value = GROUP_COLORS[0]

  // 如果是从搜索弹窗触发的，创建后自动添加
  if (showNewGroupFromSearch.value && searchResult.value) {
    const newGroup = groupStore.groups[groupStore.groups.length - 1]
    if (newGroup) {
      await addToGroup(newGroup.id)
    }
    showNewGroupFromSearch.value = false
  }
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

/* ── Section ── */

.section {
  border-bottom: 1px solid var(--border-light);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 3px solid var(--stock-up);
  background: var(--bg-hover);
  cursor: pointer;
  user-select: none;
}

.group-section .section-header {
  cursor: default;
}

.section-title {
  font-size: var(--font-size-base);
  font-weight: bold;
  color: var(--text-primary);
  flex: 1;
}

.section-count {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--bg-active);
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.collapse-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  padding: 0 4px;
}

.group-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.group-action-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: color 0.2s;
}

.group-action-btn:hover {
  color: var(--text-secondary);
}

.group-action-btn--danger:hover {
  color: var(--stock-up);
}

/* ── Watchlist Items ── */

.watchlist-items, .group-members {
  overflow-y: auto;
}

.watchlist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px var(--spacing-md);
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
  align-items: center;
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
  font-family: var(--font-mono);
}

.item-group-badges {
  display: flex;
  gap: 2px;
}

.group-badge {
  width: 8px;
  height: 8px;
  border-radius: 50%;
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

.move-btns {
  display: flex;
  gap: 2px;
}

.move-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  transition: color 0.2s;
}

.move-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

.remove-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: 2px 6px;
  margin-left: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: color 0.2s;
}

.remove-btn:hover {
  color: var(--stock-up);
}

/* ── 特别关注 ── */

.special-watch-section {
  background: var(--bg-primary);
}

.section-header--special {
  border-left-color: #fac858;
  background: rgba(250, 200, 88, 0.08);
}

.section-header--special .section-title {
  color: #d4a017;
}

.star-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-md);
  color: var(--text-muted);
  padding: 2px 4px;
  transition: color 0.2s;
}

.star-btn:hover {
  color: #fac858;
}

.star-btn--active {
  color: #fac858;
}

.picker-btn--special {
  border-left: 3px solid #fac858;
  color: #d4a017;
  font-weight: bold;
}

/* ── 编辑分组 ── */

.group-edit-inline, .create-group-form {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.edit-input {
  width: 100%;
  padding: 6px var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  background: var(--bg-primary);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.edit-input:focus {
  outline: none;
  border-color: var(--border-focus);
}

.color-picker-row {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.color-pick {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color 0.2s;
}

.color-pick.active {
  border-color: var(--text-primary);
}

.edit-save-btn {
  padding: 6px var(--spacing-md);
  border: 1px solid var(--stock-up);
  border-radius: var(--radius-sm);
  background: var(--stock-up);
  color: var(--bg-primary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: bold;
}

.edit-cancel-btn {
  padding: 6px var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  margin-left: var(--spacing-sm);
}

/* ── 搜索后分组选择弹窗 ── */

.group-picker-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.group-picker {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-lg);
  max-width: 320px;
  width: 90%;
}

.picker-title {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-weight: bold;
  margin-bottom: var(--spacing-md);
}

.picker-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: var(--font-size-base);
  margin-bottom: var(--spacing-xs);
  transition: background 0.2s;
}

.picker-btn:hover {
  background: var(--bg-hover);
}

.picker-btn--watchlist {
  border-left: 3px solid var(--stock-up);
}

.picker-btn--new {
  border-left: 3px solid var(--text-muted);
  color: var(--text-secondary);
}

.picker-close {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-sm);
}

/* ── 创建分组 ── */

.create-group-bar {
  padding: var(--spacing-md);
}

.create-group-btn {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px dashed var(--border-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--font-size-base);
  transition: all 0.2s;
}

.create-group-btn:hover {
  border-color: var(--stock-up);
  color: var(--stock-up);
  background: var(--bg-up-tint);
}

.loading {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--text-muted);
}

.empty {
  text-align: center;
  padding: var(--spacing-lg) var(--spacing-md);
  color: var(--text-muted);
  font-size: var(--font-size-base);
}
</style>