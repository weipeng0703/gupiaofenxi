/** Axios HTTP 客户端 — 连接后端 API */
import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  },
})

// 股票数据 API
export const stocksApi = {
  search: (keyword: string) => api.get('/stocks/search', { params: { keyword } }),
  getHistKline: (code: string, period?: string, startDate?: string, endDate?: string, adjust?: string) =>
    api.get(`/stocks/${code}/hist`, { params: { period, start_date: startDate, end_date: endDate, adjust } }),
  getFull: (code: string, period?: string, startDate?: string, endDate?: string, adjust?: string) =>
    api.get(`/stocks/${code}/full`, { params: { period, start_date: startDate, end_date: endDate, adjust } }),
  getQuote: (code: string) => api.get(`/stocks/${code}/quote`),
  getIntraday: (code: string, period?: string) =>
    api.get(`/stocks/${code}/intraday`, { params: { period } }),
}

// 自选股 API
export const watchlistApi = {
  list: () => api.get('/watchlist'),
  add: (data: { stock_code: string; stock_name: string; market?: string; notes?: string }) =>
    api.post('/watchlist', data),
  remove: (id: number) => api.delete(`/watchlist/${id}`),
  update: (id: number, data: { notes?: string; is_active?: boolean; is_special_watch?: boolean }) =>
    api.patch(`/watchlist/${id}`, data),
}

// 信号 API
export const signalsApi = {
  list: (params?: { stock_code?: string; signal_type?: string; unread_only?: boolean; limit?: number }) =>
    api.get('/signals', { params }),
  get: (id: number) => api.get(`/signals/${id}`),
  markRead: (id: number) => api.patch(`/signals/${id}/read`),
  generateTest: (stockCode: string, count?: number) =>
    api.post(`/signals/test/${stockCode}`, null, { params: { count: count || 5 } }),
  generateSpecialWatchTest: () => api.post('/signals/test/special-watch'),
}

// 策略 API
export const strategiesApi = {
  list: () => api.get('/strategies'),
  get: (id: number) => api.get(`/strategies/${id}`),
  create: (data: { name: string; description?: string; config_yaml: string }) =>
    api.post('/strategies', data),
  update: (id: number, data: { description?: string; config_yaml?: string; is_active?: boolean }) =>
    api.patch(`/strategies/${id}`, data),
  delete: (id: number) => api.delete(`/strategies/${id}`),
}

// 分组 API
export const groupsApi = {
  list: () => api.get('/groups'),
  create: (data: { name: string; color?: string }) => api.post('/groups', data),
  update: (id: number, data: { name?: string; color?: string }) => api.patch(`/groups/${id}`, data),
  delete: (id: number) => api.delete(`/groups/${id}`),
  getMembers: (groupId: number) => api.get(`/groups/${groupId}/members`),
  addMember: (groupId: number, data: { stock_code: string; stock_name: string; market?: string }) =>
    api.post(`/groups/${groupId}/members`, data),
  removeMember: (groupId: number, stockCode: string) => api.delete(`/groups/${groupId}/members/${stockCode}`),
  moveMember: (groupId: number, stockCode: string, direction: 'up' | 'down') =>
    api.patch(`/groups/${groupId}/members/${stockCode}/move`, { stock_code: stockCode, direction }),
}

export default api