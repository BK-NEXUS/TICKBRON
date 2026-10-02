import { SVGProps } from 'react'

/**
 * Lightweight inline SVG icon set (no third-party dependency).
 *
 * Replaces emoji used for UI decoration so icons inherit `currentColor`,
 * scale with text, and stay visually consistent with the design system.
 * Paths are simple 24x24 outlines styled after common open-source sets.
 */
export type IconName =
  | 'building'
  | 'home'
  | 'villa'
  | 'city'
  | 'badge-check'
  | 'shield'
  | 'headset'
  | 'star'
  | 'globe'
  | 'smartphone'
  | 'map-pin'
  | 'search'
  | 'calendar'
  | 'heart'
  | 'lock'
  | 'check'
  | 'arrow-right'
  | 'chevron-down'
  | 'list'
  | 'map'
  | 'eye'
  | 'eye-off'
  | 'wifi'
  | 'parking'
  | 'snowflake'
  | 'flame'
  | 'elevator'
  | 'users'
  | 'bed'
  | 'bath'
  | 'clock'
  | 'credit-card'
  | 'check-circle'
  | 'chart'
  | 'plus'
  | 'dollar'
  | 'user'
  | 'bell'
  | 'ban'

const PATHS: Record<IconName, string> = {
  building:
    'M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M4 21h16M4 21h16M16 9h2a2 2 0 0 1 2 2v10M8 7h2M8 11h2M8 15h2M12 7h0M12 11h0M12 15h0',
  home: 'M3 10.5 12 3l9 7.5M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5',
  villa:
    'M3 21h18M4 21V11l8-6 8 6v10M9 21v-6h6v6M9 12h.01M15 12h.01',
  city:
    'M3 21h18M5 21V7l5-3v17M14 21V9l5-2v14M8 9h.01M8 13h.01M8 17h.01M17 12h.01M17 16h.01',
  'badge-check':
    'M12 2.5l2.2 1.6 2.7-.2 1 2.5 2.4 1.3-.6 2.6.6 2.6-2.4 1.3-1 2.5-2.7-.2L12 21.5l-2.2-1.6-2.7.2-1-2.5-2.4-1.3.6-2.6-.6-2.6 2.4-1.3 1-2.5 2.7.2L12 2.5zM9 12l2 2 4-4',
  shield: 'M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3zM9 12l2 2 4-4',
  headset:
    'M4 13v-1a8 8 0 0 1 16 0v1M4 13h2a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-5zM20 13h-2a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-5zM18 18v1a3 3 0 0 1-3 3h-2',
  star: 'M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9L12 3.5z',
  globe:
    'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c2.5 2.5 3.8 5.6 3.8 9S14.5 18.5 12 21c-2.5-2.5-3.8-5.6-3.8-9S9.5 5.5 12 3z',
  smartphone:
    'M7 2.5h10a1.5 1.5 0 0 1 1.5 1.5v16a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 20V4A1.5 1.5 0 0 1 7 2.5zM10 18.5h4',
  'map-pin':
    'M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
  search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3',
  calendar:
    'M7 3v3M17 3v3M4 8.5h16M5 5.5h14a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6.5a1 1 0 0 1 1-1z',
  heart:
    'M12 20s-7-4.4-7-9.5A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 7 3.5C19 15.6 12 20 12 20z',
  lock: 'M7 11V8a5 5 0 0 1 10 0v3M6 11h12a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1z',
  check: 'M4.5 12.5l5 5 10-11',
  'arrow-right': 'M4 12h15M13 6l6 6-6 6',
  'chevron-down': 'M6 9l6 6 6-6',
  list: 'M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01',
  map: 'M9 4 3.5 6.5v13L9 17l6 2.5 5.5-2.5v-13L15 6.5 9 4zM9 4v13M15 6.5v13',
  eye: 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  'eye-off':
    'M4 4l16 16M9.9 5.9A9.5 9.5 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3.3 4.1M6.4 8A17 17 0 0 0 2.5 12S6 18.5 12 18.5c1 0 1.9-.2 2.7-.5M9.9 9.9a3 3 0 0 0 4.2 4.2',
  wifi: 'M2.5 8.5a15 15 0 0 1 19 0M5.5 12a10.5 10.5 0 0 1 13 0M8.5 15.5a6 6 0 0 1 7 0M12 19h.01',
  parking: 'M8 20V4h4.5a4.5 4.5 0 0 1 0 9H8M6 4h9.5a6.5 6.5 0 0 1 0 13',
  snowflake:
    'M12 2v20M4.2 7l15.6 10M19.8 7 4.2 17M12 6l2.5-2.5M12 6 9.5 3.5M12 18l2.5 2.5M12 18l-2.5 2.5M5.5 9.5 3 9M5.5 9.5 5 7M18.5 14.5 21 15M18.5 14.5 19 17M18.5 9.5 21 9M18.5 9.5 19 7M5.5 14.5 3 15M5.5 14.5 5 17',
  flame: 'M12 3c2 3 1 5 0 6.5C10.5 11.5 9 13 9 15a3 3 0 0 0 6 0c0-1-.4-1.9-1-2.7 2 1 3 2.9 3 5.2a6 6 0 0 1-12 0C6 13 9 10 12 3z',
  elevator:
    'M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM12 3v18M9 9l0 0M9 8.5l-1.5 2h3l-1.5-2M15 15l0 0M15 14.5l-1.5 2h3l-1.5-2',
  users: 'M16 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 17.5V19M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM20 19v-1.5a3.5 3.5 0 0 0-2.6-3.4M15.5 4.2a3.5 3.5 0 0 1 0 6.6',
  bed: 'M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 14h18M3 18h18M7 10V7a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v3',
  bath: 'M4 12h16a1 1 0 0 1 1 1 6 6 0 0 1-6 6H9a6 6 0 0 1-6-6 1 1 0 0 1 1-1zM7 12V6a2 2 0 0 1 4 0M6 19l-1 2M18 19l1 2',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
  'credit-card':
    'M3 7.5A1.5 1.5 0 0 1 4.5 6h15A1.5 1.5 0 0 1 21 7.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 16.5v-9zM3 10h18M6.5 14.5h3',
  'check-circle': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8.5 12l2.5 2.5 4.5-5',
  chart: 'M4 20h16M7 16v-5M12 16V8M17 16v-7',
  plus: 'M12 5v14M5 12h14',
  dollar: 'M12 2v20M16.5 6.5H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H7',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM5 20v-1a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v1',
  bell: 'M18 9a6 6 0 1 0-12 0c0 5-2 6-2 6h16s-2-1-2-6M10.5 20a2 2 0 0 0 3 0',
  ban: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM5.6 5.6l12.8 12.8',
}

export interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: number
  /** Accessible label. When omitted the icon is marked decorative. */
  title?: string
}

export function Icon({ name, size = 20, title, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      focusable="false"
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <path d={PATHS[name]} />
    </svg>
  )
}

export default Icon
