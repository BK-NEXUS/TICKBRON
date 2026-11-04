import type { Theme } from '../theme/context'

export type GlobeColors = { sphere: string; lines: string; arcs: string; dot: string; opacity: number }

export function globeColors(theme: Theme): GlobeColors {
  return theme === 'dark'
    ? { sphere: '#102a55', lines: '#4f8cff', arcs: '#8fb6ff', dot: '#ffffff', opacity: 0.9 }
    : { sphere: '#dfe8ff', lines: '#1d4ed8', arcs: '#1d4ed8', dot: '#0b2a7a', opacity: 0.85 }
}
