/** 中国股市颜色习惯：红涨绿跌 */
export const STOCK_COLORS = {
  up: '#ef232a',      // 红色 — 价格上涨
  down: '#14b143',    // 绿色 — 价格下跌
  flat: '#999999',    // 灰色 — 无变化
}

export const INDICATOR_COLORS = {
  rsi: '#5470c6',     // RSI 蓝色
  kdj_k: '#fac858',   // K 线黄色
  kdj_d: '#5470c6',   // D 线蓝色
  kdj_j: '#ee6666',   // J 线紫红色
}

/** 根据收盘价和开盘价判断涨跌颜色 */
export function getStockColor(close: number, open: number): string {
  if (close > open) return STOCK_COLORS.up
  if (close < open) return STOCK_COLORS.down
  return STOCK_COLORS.flat
}

/** 成交量柱状图颜色（根据收盘价 vs 前收盘价） */
export function getVolumeColor(close: number, prevClose: number): string {
  if (close > prevClose) return STOCK_COLORS.up
  if (close < prevClose) return STOCK_COLORS.down
  return STOCK_COLORS.flat
}

/** 格式化涨跌幅显示 */
export function formatChange(changePct: number): string {
  const sign = changePct > 0 ? '+' : ''
  return `${sign}${changePct.toFixed(2)}%`
}

/** 格式化价格显示 */
export function formatPrice(price: number): string {
  return price.toFixed(2)
}

/** 格式化成交量（万/亿） */
export function formatVolume(volume: number): string {
  if (volume >= 100000000) return `${(volume / 100000000).toFixed(2)}亿`
  if (volume >= 10000) return `${(volume / 10000).toFixed(2)}万`
  return volume.toFixed(0)
}