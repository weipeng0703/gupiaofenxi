/** ECharts K 线图配置构建器 — 四面板同步图表 */
import type { EChartsOption } from 'echarts'
import type { KlinePoint, IndicatorData } from '@/types/stock'
import { STOCK_COLORS, INDICATOR_COLORS, getVolumeColor } from '@/utils/colorUtils'

/**
 * 根据 containerWidth 计算 ECharts grid 偏移量
 * 小屏幕用百分比避免 Y 轴标签溢出，大屏幕用像素保证精确对齐
 */
function getGridOffsets(containerWidth?: number) {
  if (containerWidth && containerWidth <= 768) {
    return { left: '12%', right: '8%' }
  }
  if (containerWidth && containerWidth <= 1024) {
    return { left: 60, right: 30 }
  }
  return { left: 80, right: 40 }
}

/**
 * 构建 K 线四面板完整配置
 *
 * 面板布局：
 * - Grid 0: K 线蜡烛图 + MA 线叠加 (43% 高度)
 * - Grid 1: 成交量柱状图 (12% 高度)
 * - Grid 2: RSI 曲线 (11% 高度)
 * - Grid 3: KDJ 三线 (11% 高度)
 */
export function buildKlineOption(kline: KlinePoint[], indicators: IndicatorData, containerWidth?: number): EChartsOption {
  if (!kline.length) return {}

  const offsets = getGridOffsets(containerWidth)
  const isSmall = containerWidth && containerWidth <= 768
  const leftPx = typeof offsets.left === 'number' ? offsets.left : 60

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

  // RSI 多周期线数据
  const rsiSeries: EChartsOption['series'] = []
  const rsiColors: Record<string, string> = {
    RSI6: '#2d2d2d',
    RSI12: '#f59e0b',
    RSI24: '#8b5cf6',
  }
  if (indicators.rsi) {
    for (const [name, data] of Object.entries(indicators.rsi)) {
      rsiSeries.push({
        name,
        type: 'line',
        data,
        xAxisIndex: 2,
        yAxisIndex: 2,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: rsiColors[name] || '#aaa' },
      })
    }
  }

  const option: EChartsOption = {
    animation: false,
    graphic: [
      {
        type: 'text',
        left: leftPx + 5,
        top: '50%',
        style: { text: 'VOL', fontSize: isSmall ? 9 : 11, fill: '#888', fontWeight: 'bold' },
      },
      {
        type: 'text',
        left: leftPx + 5,
        top: '63%',
        style: {
          text: 'RSI (6,12,24)',
          fontSize: isSmall ? 9 : 11,
          fill: '#888',
          fontWeight: 'bold',
        },
      },
      {
        type: 'text',
        left: leftPx + 5,
        top: '80%',
        style: {
          text: 'KDJ (9,3,3)',
          fontSize: isSmall ? 9 : 11,
          fill: '#888',
          fontWeight: 'bold',
        },
      },
    ],
    legend: {
      data: ['K线', ...Object.keys(indicators.ma || {}), ...Object.keys(indicators.rsi || {}), 'K', 'D', 'J'],
      top: 5,
      left: offsets.left,
      textStyle: { fontSize: isSmall ? 9 : 11 },
      itemWidth: 14,
      itemGap: isSmall ? 8 : 12,
    },
    axisPointer: {
      link: [{ xAxisIndex: [0, 1, 2, 3] }],
    },
    grid: [
      { left: offsets.left, right: offsets.right, top: 40, height: '38%' },
      { left: offsets.left, right: offsets.right, top: '50%', height: '10%' },
      { left: offsets.left, right: offsets.right, top: '63%', height: '14%' },
      { left: offsets.left, right: offsets.right, top: '80%', height: '14%' },
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 1, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 2, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: dates, gridIndex: 3, axisLabel: { show: true, fontSize: isSmall ? 9 : 10 } },
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true, splitLine: { show: true }, axisLabel: { fontSize: isSmall ? 9 : 10 } },
      { type: 'value', gridIndex: 1, splitNumber: 2, axisLabel: { show: true, fontSize: isSmall ? 9 : 10 } },
      { type: 'value', gridIndex: 2, min: 0, max: 100, splitNumber: 2, axisLabel: { fontSize: isSmall ? 9 : 10 } },
      { type: 'value', gridIndex: 3, splitNumber: 2, axisLabel: { fontSize: isSmall ? 9 : 10 } },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1, 2, 3],
        start: 70,
        end: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1, 2, 3],
        bottom: 5,
        height: isSmall ? 15 : 20,
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      confine: true,
      formatter: (params: unknown) => formatTooltip(params, kline, indicators),
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
          color: STOCK_COLORS.up,
          color0: STOCK_COLORS.down,
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
      // ── 面板 2: RSI 多周期 ──
      ...rsiSeries,
      // RSI 超买超卖参考线
      {
        name: 'RSI参考线',
        type: 'line',
        data: [],
        xAxisIndex: 2,
        yAxisIndex: 2,
        markLine: {
          silent: true,
          symbol: 'none',
          label: { fontSize: isSmall ? 8 : 10 },
          data: [
            { yAxis: 30, name: '超卖', lineStyle: { type: 'dashed', color: STOCK_COLORS.down }, label: { formatter: '超卖 30', position: 'insideEndTop', color: STOCK_COLORS.down } },
            { yAxis: 50, name: '中轴', lineStyle: { type: 'dashed', color: '#ccc' }, label: { formatter: '50', position: 'insideEndTop', color: '#aaa' } },
            { yAxis: 70, name: '超买', lineStyle: { type: 'dashed', color: STOCK_COLORS.up }, label: { formatter: '超买 70', position: 'insideEndTop', color: STOCK_COLORS.up } },
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
      // KDJ 超买超卖参考线
      {
        name: 'KDJ参考线',
        type: 'line',
        data: [],
        xAxisIndex: 3,
        yAxisIndex: 3,
        markLine: {
          silent: true,
          symbol: 'none',
          label: { fontSize: isSmall ? 8 : 10 },
          data: [
            { yAxis: 20, name: '超卖', lineStyle: { type: 'dashed', color: '#ccc' }, label: { formatter: '20', position: 'insideEndTop', color: '#aaa' } },
            { yAxis: 80, name: '超买', lineStyle: { type: 'dashed', color: '#ccc' }, label: { formatter: '80', position: 'insideEndTop', color: '#aaa' } },
          ],
        },
      },
    ],
  }

  return option
}

/** Tooltip 格式化 — 分组显示 */
function formatTooltip(params: unknown, kline: KlinePoint[], indicators: IndicatorData): string {
  const p = params as Array<{ seriesName: string; dataIndex: number; value: unknown; axisValue: string }>
  if (!Array.isArray(p) || !p.length) return ''

  const idx = p[0]?.dataIndex ?? 0
  const k = kline[idx]
  if (!k) return ''

  const dateStr = p[0]?.axisValue || k.date
  const color = k.close > k.open ? STOCK_COLORS.up : STOCK_COLORS.down

  // 计算涨跌幅
  let changePct: number | null = null
  if (k.change_pct != null) {
    changePct = k.change_pct
  } else if (idx > 0) {
    const prevClose = kline[idx - 1]?.close
    if (prevClose) {
      changePct = ((k.close - prevClose) / prevClose) * 100
    }
  }
  const changePctStr = changePct != null
    ? `<span style="color:${changePct >= 0 ? STOCK_COLORS.up : STOCK_COLORS.down}">${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%</span>`
    : '-'

  const sep = '<div style="border-top:1px solid #eee;margin:3px 0"></div>'

  let html = `<div style="font-size:12px;line-height:1.6"><b>${dateStr}</b><br/>`
  html += `开: ${k.open.toFixed(2)}  收: <span style="color:${color}">${k.close.toFixed(2)}</span><br/>`
  html += `高: ${k.high.toFixed(2)}  低: ${k.low.toFixed(2)}<br/>`
  html += `涨跌: ${changePctStr}<br/>`
  html += `量: ${k.volume?.toLocaleString() || '-'}`

  // MA 指标组
  const maData = indicators.ma
  if (maData) {
    const maItems: string[] = []
    for (const [name, values] of Object.entries(maData)) {
      const v = values[idx]
      if (v != null) maItems.push(`${name}: ${v.toFixed(2)}`)
    }
    if (maItems.length) {
      html += sep
      html += maItems.join('  ')
    }
  }

  // RSI 指标组
  const rsiData = indicators.rsi
  if (rsiData) {
    const rsiItems: string[] = []
    for (const [name, values] of Object.entries(rsiData)) {
      const v = values[idx]
      if (v != null) rsiItems.push(`${name}: ${v.toFixed(2)}`)
    }
    if (rsiItems.length) {
      html += sep
      html += rsiItems.join('  ')
    }
  }

  // KDJ 指标组
  const kdjData = indicators.kdj
  if (kdjData) {
    const kdjItems: string[] = []
    for (const [name, values] of Object.entries(kdjData)) {
      const v = values[idx]
      if (v != null) kdjItems.push(`${name}: ${v.toFixed(2)}`)
    }
    if (kdjItems.length) {
      html += sep
      html += kdjItems.join('  ')
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
