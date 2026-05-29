<template>
  <div ref="chartContainer" class="kline-chart" :style="{ height: chartHeight }"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { KlinePoint, IndicatorData, SignalItem } from '@/types/stock'
import { buildKlineOption } from '@/services/chartConfig'

const props = defineProps<{
  kline: KlinePoint[]
  indicators: IndicatorData
  signals?: SignalItem[]
  height?: string
}>()

const chartContainer = ref<HTMLDivElement>()
const chartHeight = ref(props.height || '600px')
let chartInstance: echarts.ECharts | null = null

/** 初始化 ECharts 实例 */
function initChart() {
  if (!chartContainer.value) return
  chartInstance = echarts.init(chartContainer.value, undefined, { renderer: 'canvas' })
  updateChart()
}

/** 更新图表数据 */
function updateChart() {
  if (!chartInstance || !props.kline.length) return

  const option = buildKlineOption(props.kline, props.indicators)

  // 如果有信号数据，在 K 线上添加买卖信号标注
  if (props.signals && props.signals.length) {
    const markPoints: any[] = []
    for (const signal of props.signals) {
      // 找到信号对应的 K 线数据索引
      const idx = props.kline.findIndex((k) => k.date === signal.timestamp)
      if (idx >= 0) {
        markPoints.push({
          name: `${signal.signal_type} ${signal.strategy_name}`,
          coord: [signal.timestamp, signal.signal_type === 'BUY' ? props.kline[idx].low : props.kline[idx].high],
          value: signal.signal_type,
          symbol: signal.signal_type === 'BUY' ? 'pin' : 'triangle',
          symbolSize: 30,
          itemStyle: {
            color: signal.signal_type === 'BUY' ? '#ef232a' : '#14b143',
          },
          label: {
            show: true,
            formatter: signal.signal_type === 'BUY' ? '买' : '卖',
            fontSize: 12,
            color: '#fff',
          },
        })
      }
    }

    // 在 K 线系列上添加 markPoint
    if (markPoints.length && option.series) {
      const klineSeries = (option.series as any[]).find((s) => s.type === 'candlestick')
      if (klineSeries) {
        klineSeries.markPoint = {
          data: markPoints,
          animation: false,
        }
      }
    }
  }

  chartInstance.setOption(option, { notMerge: true })
}

/** 监听数据变化更新图表 */
watch(() => [props.kline, props.indicators], () => {
  updateChart()
}, { deep: true })

/** 监听窗口大小变化 */
function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.kline-chart {
  width: 100%;
  min-height: 500px;
}
</style>