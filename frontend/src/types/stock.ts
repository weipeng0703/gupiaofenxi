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
  rsi: (number | null)[]
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