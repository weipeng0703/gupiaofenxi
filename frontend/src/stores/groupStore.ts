/** 分组 Store — 管理股票分组和成员 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StockGroup, StockGroupMember, StockGroupCreate } from '@/types/stock'
import { groupsApi } from '@/services/api'

export const useGroupStore = defineStore('group', () => {
  const groups = ref<StockGroup[]>([])
  const members = ref<Map<number, StockGroupMember[]>>(new Map())
  const loading = ref(false)

  async function loadGroups() {
    loading.value = true
    try {
      const { data } = await groupsApi.list()
      groups.value = data
      // 加载每个分组的成员
      for (const g of data) {
        await loadMembers(g.id)
      }
    } catch (e) {
      console.error('加载分组失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadMembers(groupId: number) {
    try {
      const { data } = await groupsApi.getMembers(groupId)
      members.value.set(groupId, data)
    } catch (e) {
      console.error('加载分组成员失败:', e)
    }
  }

  async function createGroup(data: StockGroupCreate) {
    try {
      const { data: group } = await groupsApi.create(data)
      groups.value.push(group)
      members.value.set(group.id, [])
    } catch (e) {
      console.error('创建分组失败:', e)
    }
  }

  async function deleteGroup(groupId: number) {
    try {
      await groupsApi.delete(groupId)
      groups.value = groups.value.filter(g => g.id !== groupId)
      members.value.delete(groupId)
    } catch (e) {
      console.error('删除分组失败:', e)
    }
  }

  async function updateGroup(groupId: number, data: { name?: string; color?: string }) {
    try {
      const { data: updated } = await groupsApi.update(groupId, data)
      const idx = groups.value.findIndex(g => g.id === groupId)
      if (idx >= 0) {
        groups.value[idx] = updated
      }
    } catch (e) {
      console.error('更新分组失败:', e)
    }
  }

  async function addMember(groupId: number, stockCode: string, stockName: string, market: string = 'A') {
    try {
      const { data: member } = await groupsApi.addMember(groupId, {
        stock_code: stockCode,
        stock_name: stockName,
        market,
      })
      const current = members.value.get(groupId) || []
      members.value.set(groupId, [...current, member])
      // 更新 member_count
      const g = groups.value.find(g => g.id === groupId)
      if (g) {
        g.member_count = (g.member_count || 0) + 1
      }
    } catch (e) {
      console.error('添加分组成员失败:', e)
      throw e // 让组件层处理提示
    }
  }

  async function removeMember(groupId: number, stockCode: string) {
    try {
      await groupsApi.removeMember(groupId, stockCode)
      const current = members.value.get(groupId) || []
      members.value.set(groupId, current.filter(m => m.stock_code !== stockCode))
      // 更新 member_count
      const g = groups.value.find(g => g.id === groupId)
      if (g) {
        g.member_count = Math.max(0, (g.member_count || 0) - 1)
      }
    } catch (e) {
      console.error('移除分组成员失败:', e)
    }
  }

  async function moveMember(groupId: number, stockCode: string, direction: 'up' | 'down') {
    try {
      await groupsApi.moveMember(groupId, stockCode, direction)
      // 重新加载成员列表获取最新排序
      await loadMembers(groupId)
    } catch (e) {
      console.error('移动分组成员失败:', e)
    }
  }

  function getMembers(groupId: number): StockGroupMember[] {
    return members.value.get(groupId) || []
  }

  /** 判断一个标的是否在指定分组中 */
  function isInGroup(groupId: number, stockCode: string): boolean {
    const list = members.value.get(groupId) || []
    return list.some(m => m.stock_code === stockCode)
  }

  /** 判断一个标的是否在任意分组中 */
  function isInAnyGroup(stockCode: string): number[] {
    const groupIds: number[] = []
    for (const [gid, list] of members.value.entries()) {
      if (list.some(m => m.stock_code === stockCode)) {
        groupIds.push(gid)
      }
    }
    return groupIds
  }

  return {
    groups, members, loading,
    loadGroups, loadMembers,
    createGroup, deleteGroup, updateGroup,
    addMember, removeMember, moveMember,
    getMembers, isInGroup, isInAnyGroup,
  }
})