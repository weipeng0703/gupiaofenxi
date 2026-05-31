import { useBreakpoints } from '@vueuse/core'

const breakpoints = useBreakpoints({
  mobile: 768,
  tablet: 1024,
})

export function useResponsive() {
  const isMobile = breakpoints.smallerOrEqual('mobile')    // ≤ 768px
  const isTablet = breakpoints.between('mobile', 'tablet') // 769–1024px (exclusive ends)
  const isDesktop = breakpoints.greaterOrEqual('tablet')   // ≥ 1024px

  return { isMobile, isTablet, isDesktop }
}