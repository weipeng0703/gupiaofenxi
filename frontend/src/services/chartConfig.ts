/** ECharts K 线图配置构建器 — 四面板同步图表 */
import type { EChartsOption } from 'echarts'
import type { KlinePoint, IndicatorData } from '@/types/stock'
import { STOCK_COLORS, INDICATOR_COLORS, getStockColor, getVolumeColor } from '@/utils/colorUtils'

/**
 * 构建 K 线四面板完整配置
 *
 * 面板布局：
 * - Grid 0: K 线蜡烛图 + MA 线叠加 (50% 高度)
 * - Grid 1: 成交量柱状图 (16% 高度)
 * - Grid 2: RSI 曲线 (14% 高度)
 * - Grid 3: KDJ 三线 (14% 高度)
 */
export function buildKlineOption(kline: KlinePoint[], indicators: IndicatorData): EChartsOption {
  if (!kline.length) return {}

  const dates = kline.map((k) => k.date)
  // ECharts candlestick 数据格式: [open, close, low, high]
  const ohlc = kline.map((k) => [k.open, k.close, k.low, k.high])

  // 成交量数据 — 每条 [volume, color]
  const volumes = kline.map((k, i) => {
    const prevClose = i > 0 ? kline[i - 1]?.close ?? k.open : k.open
    return {
      value: k.volume,
      itemStyle: { color: getVolumeColor(k.close, prevClose) },
    }
  })

  // MA 数据
  const maSeries: EChartsOption['series'] = []
  if (indicators.ma) {
    const maColors: Record<string, string> = {
      MA5: '#fac858',
      MA10: '#ee6666',
      MA20: '#5470c6',
      MA60: '#91cc75',
    }
    for (const [name, data] of Object.entries(indicators.ma)) {
      maSeries.push({
        name,
        type: 'line',
        data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1, color: maColors[name] || '#aaa' },
      })
    }
  }

  // 信号标记 — 在 K 线上标注买卖信号点
  const signalMarkPoints: Record<string, unknown[]> = { buy: [], sell: [] }
  // (此处留空，信号数据将通过 store 动态注入)

  const option: EChartsOption = {
    animation: false, // 大数据集性能优化
    legend: {
      data: ['K线', ...Object.keys(indicators.ma || {}), '成交量', 'RSI', 'K', 'D', 'J'],
      top: 5,
      left: 80,
    },
    axisPointer: {
      link: [{ xAxisIndex: [0, 1, 2, 3] }], // 四面板 x 轴联动
    },
    grid: [
      { left: 80, right: 40, top: 40, height: '45%' },         // K 线 + MA
      { left: 80, right: 40, top: '55%', height: '14%' },       // 成交量
      { left: 80, right: 40, top: '72%', height: '12%' },       // RSI
      { left: 80, right: 40, top: '87%', height: '11%' },       // KDJ
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 1, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 2, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 3, axisLabel: { show: true, fontSize: 10 } },
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true, splitLine: { show: true } },           // 价格
      { type: 'value', gridIndex: 1, splitNumber: 2, axisLabel: { show: true, fontSize: 10 } }, // 成交量
      { type: 'value', gridIndex: 2, min: 0, max: 100, splitNumber: 4, axisLabel: { fontSize: 10 } }, // RSI
      { type: 'value', gridIndex: 3, axisLabel: { fontSize: 10 } },                       // KDJ
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1, 2, 3],
        start: 70, // 默认显示最近 30% 的数据
        end: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1, 2, 3],
        bottom: 5,
        height: 20,
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: unknown) => formatTooltip(params, kline),
    },
    series: [
      // ── 面板 0: K 线蜡烛图 ──
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: STOCK_COLORS.up,       // 涨 — 红色填充
          color0: STOCK_COLORS.down,    // 跌 — 绿色填充
          borderColor: STOCK_COLORS.up,
          borderColor0: STOCK_COLORS.down,
        },
      },
      // ── MA 线叠加 ──
      ...maSeries,
      // ── 面板 1: 成交量 ──
      {
        name: '成交量',
        type: 'bar',
        data: volumes as unknown as number[],
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '60%',
      },
      // ── 面板 2: RSI ──
      {
        name: 'RSI',
        type: 'line',
        data: indicators.rsi,
        xAxisIndex: 2,
        yAxisIndex: 2,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: INDICATOR_COLORS.rsi, width: 1.5 },
        markLine: {
          silent: true,
          lineStyle: { type: 'dashed', color: '#aaa' },
          data: [
            { yAxis: 30, name: '超卖线(30)' },
            { yAxis: 70, name: '超买线(70)' },
          ],
        },
      },
      // ── 面板 3: KDJ ──
      {
        name: 'K',
        type: 'line',
        data: indicators.kdj?.K || [],
        xAxisIndex: 3,
        yAxisIndex: 3,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: INDICATOR_COLORS.kdj_k, width: 1.5 },
      },
      {
        name: 'D',
        type: 'line',
        data: indicators.kdj?.D || [],
        xAxisIndex: 3,
        yAxisIndex: 3,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: INDICATOR_COLORS.kdj_d, width: 1.5 },
      },
      {
        name: 'J',
        type: 'line',
        data: indicators.kdj?.J || [],
        xAxisIndex: 3,
        yAxisIndex: 3,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: INDICATOR_COLORS.kdj_j, width: 1.5 },
      },
    ],
  }

  return option
}

/** Tooltip 格式化 */
function formatTooltip(params: unknown, kline: KlinePoint[]): string {
  const p = params as Array<{ seriesName: string; dataIndex: number; value: unknown; axisValue: string }>
  if (!Array.isArray(p) || !p.length) return ''

  const idx = p[0]?.dataIndex ?? 0
  const k = kline[idx]
  if (!k) return ''

  const dateStr = p[0]?.axisValue || k.date
  const color = k.close > k.open ? STOCK_COLORS.up : STOCK_COLORS.down

  let html = `<div style="font-size:12px"><b>${dateStr}</b><br/>`
  html += `开: ${k.open}  收: <span style="color:${color}">${k.close}</span><br/>`
  html += `高: ${k.high}  低: ${k.low}<br/>`
  html += `量: ${k.volume?.toLocaleString() || '-'}<br/>`

  // 添加指标值
  for (const item of p) {
    if (item.seriesName !== 'K线' && item.value != null && item.value !== '-') {
      html += `${item.seriesName}: ${item.value}<br/>`
    }
  }

  html += '</div>'
  return html
}

/** 周期切换标签选项 */
export const PERIOD_OPTIONS = [
  { label: '5分', value: '5min' },
  { label: '15分', value: '15min' },
  { label: '30分', value: '30min' },
  { label: '60分', value: '60min' },
  { label: '日K', value: 'daily' },
  { label: '周K', value: 'weekly' },
  { label: '月K', value: 'monthly' },
] as const