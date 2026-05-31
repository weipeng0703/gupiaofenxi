<template>
  <div ref="chartContainer" class="kline-chart"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useResizeObserver, useDebounceFn } from '@vueuse/core'
import * as echarts from 'echarts'
import type { KlinePoint, IndicatorData, SignalItem } from '@/types/stock'
import { buildKlineOption } from '@/services/chartConfig'

const props = defineProps<{
  kline: KlinePoint[]
  indicators: IndicatorData
  signals?: SignalItem[]
}>()

const chartContainer = ref<HTMLDivElement>()
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

  const width = chartContainer.value?.clientWidth ?? 1024
  const option = buildKlineOption(props.kline, props.indicators, width)

  // 如果有信号数据，在 K 线上添加买卖信号标注
  if (props.signals && props.signals.length) {
    const markPoints: any[] = []
    for (const signal of props.signals) {
      // 找到信号对应的 K 线数据索引
      const idx = props.kline.findIndex((k) => k.date === signal.timestamp)
      if (idx >= 0) {
        markPoints.push({
          name: `${signal.signal_type} ${signal.strategy_name}`,
          coord: [signal.timestamp, signal.signal_type === 'BUY' ? (props.kline[idx]?.low ?? 0) : (props.kline[idx]?.high ?? 0)],
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

/** 容器尺寸变化 → resize，加 100ms debounce */
const debouncedResize = useDebounceFn(() => {
  chartInstance?.resize()
  // 宽度变化后需要重新计算 grid 偏移
  if (props.kline.length) {
    updateChart()
  }
}, 100)

onMounted(() => {
  initChart()
  // 用 ResizeObserver 替代 window resize，响应容器级变化
  useResizeObserver(chartContainer, debouncedResize)
})

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.kline-chart {
  width: 100%;
  flex: 1;
  min-height: 500px;
}

@media (max-width: 768px) {
  .kline-chart {
    min-height: 300px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .kline-chart {
    min-height: 400px;
  }
}
</style>