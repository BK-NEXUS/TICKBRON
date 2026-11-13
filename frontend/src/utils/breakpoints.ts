// TICKBRON Plan V4 boyınsha responsive breakpoint utility leri
// 320–767px: mobil
// 768–1023px: planshet
// 1024–1439px: kompyuter
// 1440px+: úlken kompyuter

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
  
  // Mobil birinshi usıl ushın max-width query leri
  mobileOnly: `(max-width: ${BREAKPOINTS.tablet - 1}px)`,
  tabletOnly: `(min-width: ${BREAKPOINTS.tablet}px) and (max-width: ${BREAKPOINTS.desktop - 1}px)`,
  desktopOnly: `(min-width: ${BREAKPOINTS.desktop}px) and (max-width: ${BREAKPOINTS.largeDesktop - 1}px)`,
  largeDesktopOnly: `(min-width: ${BREAKPOINTS.largeDesktop}px)`,
} as const

/**
 * Házirgi breakpoint ti alıw ushın hook
 * Eskertiw: Bul ápiwayılastırılǵan nusqa. Production ushın react-breakpoints sıyaqlı
 * kitapxanadan paydalanıwdı yamasa ResizeObserver menen ámelge asırıwdı oylań
 */
export function useBreakpoint(): Breakpoint {
  if (typeof window === 'undefined') {
    return 'desktop' // SSR ushın ádetdegi
  }

  const width = window.innerWidth

  if (width >= BREAKPOINTS.largeDesktop) return 'largeDesktop'
  if (width >= BREAKPOINTS.desktop) return 'desktop'
  if (width >= BREAKPOINTS.tablet) return 'tablet'
  return 'mobile'
}

/**
 * Házirgi viewport breakpoint ke sáykes keliwin tekseriw
 */
export function useMediaQuery(query: string): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const mediaQuery = window.matchMedia(query)
  return mediaQuery.matches
}

/**
 * Belgili breakpoint ler ushın qolaylı hook lar
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
