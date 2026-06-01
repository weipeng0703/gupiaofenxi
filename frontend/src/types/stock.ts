/** TypeScript 类型定义 — 股票数据 */
export interface KlinePoint {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  amount?: number
  turnover?: number
  change_pct?: number
  change_amt?: number
}

export interface IndicatorData {
  ma: Record<string, (number | null)[]>   // { "MA5": [...], "MA10": [...], ... }
  rsi: Record<string, (number | null)[]>  // { "RSI6": [...], "RSI12": [...], "RSI24": [...] }
  kdj: {
    K: (number | null)[]
    D: (number | null)[]
    J: (number | null)[]
  }
}

export interface StockFullResponse {
  stock_code: string
  stock_name: string
  period: string
  kline: KlinePoint[]
  indicators: IndicatorData
  signals: SignalItem[]
}

export interface RealtimeQuote {
  stock_code: string
  stock_name: string
  price: number
  change_pct: number
  change_amt: number
  volume: number
  amount: number
  amplitude: number
  high: number
  low: number
  open: number
  prev_close: number
  volume_ratio: number
  turnover_rate: number
  timestamp: string
}

export interface StockSearchResult {
  stock_code: string
  stock_name: string
  market: string
}

export interface WatchlistItem {
  id: number
  stock_code: string
  stock_name: string
  market: string
  added_at: string
  is_active: boolean
  notes: string
}

export interface WatchlistAdd {
  stock_code: string
  stock_name: string
  market?: string
  notes?: string
}

export interface SignalItem {
  id: number
  stock_code: string
  strategy_name: string
  signal_type: 'BUY' | 'SELL'
  confidence: number
  indicator_values: Record<string, number>
  price: number
  timestamp: string
  is_read: boolean
}

export interface StrategyItem {
  id: number
  name: string
  description: string
  config_yaml: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** WebSocket 消息 */
export interface WSMessage {
  type: string
  payload: Record<string, unknown>
  timestamp: string
}

// ─── 股票分组 ───

export interface StockGroup {
  id: number
  name: string
  color: string
  sort_order: number
  created_at: string
  member_count: number
}

export interface StockGroupCreate {
  name: string
  color?: string
}

export interface StockGroupUpdate {
  name?: string
  color?: string
}

export interface StockGroupMember {
  stock_code: string
  stock_name: string
  market: string
  sort_order: number
  added_at: string
}

export interface StockGroupMemberAdd {
  stock_code: string
  stock_name: string
  market?: string
}

/** 分组颜色预设 */
export const GROUP_COLORS: string[] = [
  '#5470c6', // 蓝
  '#91cc75', // 绿
  '#fac858', // 黄
  '#ee6666', // 红
  '#73c0de', // 青
  '#3ba272', // 深绿
  '#fc8452', // 橙
  '#9a60b4', // 紫
  '#ea7ccc', // 粉
  '#48b8d0', // 天蓝
]