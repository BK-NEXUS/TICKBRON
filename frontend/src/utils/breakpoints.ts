// Responsive breakpoint utilities following TICKBRON Plan V4
// 320–767px: mobile
// 768–1023px: tablet
// 1024–1439px: desktop
// 1440px+: large desktop

export const BREAKPOINTS = {
  mobile: 320,
  tablet: 768,
  desktop: 1024,
  largeDesktop: 1440,
} as const

export type Breakpoint = keyof typeof BREAKPOINTS

export const MEDIA_QUERIES = {
  mobile: `(min-width: ${BREAKPOINTS.mobile}px)`,
  tablet: `(min-width: ${BREAKPOINTS.tablet}px)`,
  desktop: `(min-width: ${BREAKPOINTS.desktop}px)`,
  largeDesktop: `(min-width: ${BREAKPOINTS.largeDesktop}px)`,
  
  // Max-width queries for mobile-first approach
  mobileOnly: `(max-width: ${BREAKPOINTS.tablet - 1}px)`,
  tabletOnly: `(min-width: ${BREAKPOINTS.tablet}px) and (max-width: ${BREAKPOINTS.desktop - 1}px)`,
  desktopOnly: `(min-width: ${BREAKPOINTS.desktop}px) and (max-width: ${BREAKPOINTS.largeDesktop - 1}px)`,
  largeDesktopOnly: `(min-width: ${BREAKPOINTS.largeDesktop}px)`,
} as const

/**
 * Hook to get current breakpoint
 * Note: This is a simplified version. For production, consider using
 * a library like react-breakpoints or implement with ResizeObserver
 */
export function useBreakpoint(): Breakpoint {
  if (typeof window === 'undefined') {
    return 'desktop' // Default for SSR
  }

  const width = window.innerWidth

  if (width >= BREAKPOINTS.largeDesktop) return 'largeDesktop'
  if (width >= BREAKPOINTS.desktop) return 'desktop'
  if (width >= BREAKPOINTS.tablet) return 'tablet'
  return 'mobile'
}

/**
 * Check if current viewport matches a breakpoint
 */
export function useMediaQuery(query: string): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const mediaQuery = window.matchMedia(query)
  return mediaQuery.matches
}

/**
 * Convenience hooks for specific breakpoints
 */
export function useIsMobile(): boolean {
  return useMediaQuery(MEDIA_QUERIES.mobileOnly)
}

export function useIsTablet(): boolean {
  return useMediaQuery(MEDIA_QUERIES.tabletOnly)
}

export function useIsDesktop(): boolean {
  return useMediaQuery(MEDIA_QUERIES.desktopOnly)
}

export function useIsLargeDesktop(): boolean {
  return useMediaQuery(MEDIA_QUERIES.largeDesktopOnly)
}
