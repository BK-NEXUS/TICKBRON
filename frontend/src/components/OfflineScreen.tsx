import { useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { useOnlineStatus } from '../hooks/useOnlineStatus'

/**
 * TICKBRON's own picture: the hotel in a night cap, asleep under the moon between two palms, with a suitcase at
 * the door and a "no signal" badge. Colours follow the theme; the moving parts are named in styles/index.css.
 */
function SleepingHotel() {
  const fill = (color: string) => ({ fill: `var(${color})` })
  const line = { stroke: 'var(--color-text-primary)', fill: 'none' }
  const star = (x: number, y: number, size: number, extra: string) => (
    <path key={`${x}${y}`} className={`offline-star ${extra}`} transform={`translate(${x} ${y})`}
      d={`M0 ${-size} L${size * 0.28} ${-size * 0.28} L${size} 0 L${size * 0.28} ${size * 0.28} L0 ${size} L${-size * 0.28} ${size * 0.28} L${-size} 0 L${-size * 0.28} ${-size * 0.28} Z`}
      style={fill('--color-gold')} />
  )
  const palm = (x: number, scale: number, extra: string) => (
    <g transform={`translate(${x} 174) scale(${scale})`}>
      <g className={`offline-sway ${extra}`}>
        <path d="M0 0 C -5 -28 5 -52 0 -78" style={{ stroke: 'var(--color-gold-dark)' }} strokeWidth="6" strokeLinecap="round" fill="none" />
        {[-168, -96, -24, 148].map(angle => (
          <path key={`back${angle}`} d="M0 0 C 12 -16 38 -16 56 6 C 38 -3 14 -2 0 0 Z" transform={`translate(0 -78) rotate(${angle})`}
            style={fill('--color-gold-dark')} />
        ))}
        {[-132, -60, 12].map(angle => (
          <path key={`front${angle}`} d="M0 0 C 12 -16 38 -16 56 6 C 38 -3 14 -2 0 0 Z" transform={`translate(0 -78) rotate(${angle})`}
            style={fill('--color-gold')} />
        ))}
        <circle cx="-5" cy="-74" r="4" style={fill('--color-gold-dark')} />
        <circle cx="5" cy="-73" r="4" style={fill('--color-gold-dark')} />
      </g>
    </g>
  )
  const cloud = (x: number, y: number, extra: string) => (
    <g transform={`translate(${x} ${y})`}>
      <g className={`offline-drift ${extra}`} style={{ fill: 'var(--color-background-alt)' }}>
        <ellipse cx="0" cy="0" rx="14" ry="6" />
        <ellipse cx="-7" cy="-4" rx="8" ry="6" />
        <ellipse cx="6" cy="-5" rx="9" ry="7" />
      </g>
    </g>
  )
  return (
    <svg className="offline-art" viewBox="0 -24 240 224" width="240" height="224" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="offline-tower" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: 'var(--color-gold)' }} />
          <stop offset="1" style={{ stopColor: 'var(--color-gold-dark)', stopOpacity: 0.92 }} />
        </linearGradient>
      </defs>
      <g className="offline-moon">
        <circle cx="198" cy="-4" r="22" style={{ fill: 'var(--color-gold)', opacity: 0.14 }} />
        <path d="M198 -20 a16 16 0 1 0 14 24 a13 13 0 1 1 -14 -24 z" style={fill('--color-gold')} />
      </g>
      {star(26, -8, 5, '')}
      {star(80, -16, 4, 'offline-star--2')}
      {star(124, -6, 3.5, 'offline-star--3')}
      {star(224, 34, 4, 'offline-star--2')}
      {star(14, 34, 3, 'offline-star--3')}
      {cloud(178, 70, '')}
      {cloud(34, 108, 'offline-drift--slow')}
      <ellipse cx="120" cy="178" rx="100" ry="9" style={fill('--color-border')} />
      {palm(42, 0.95, '')}
      {palm(198, 0.78, 'offline-sway--slow')}
      {[[58, 178], [172, 178], [214, 178]].map(([x, y]) => (
        <path key={x} d={`M${x} ${y} l-3 -8 M${x} ${y} l1 -10 M${x} ${y} l5 -7`} style={{ stroke: 'var(--color-gold-dark)' }}
          strokeWidth="2" strokeLinecap="round" fill="none" />
      ))}
      <g transform="translate(0 4)">
        <g className="offline-breathe">
          <rect x="66" y="94" width="32" height="80" rx="5" style={fill('--color-gold-dark')} />
          <rect x="142" y="104" width="32" height="70" rx="5" style={fill('--color-gold-dark')} />
          <rect x="92" y="52" width="56" height="122" rx="9" style={{ fill: 'url(#offline-tower)' }} />
          <rect x="97" y="58" width="5" height="108" rx="2.5" style={{ fill: 'var(--color-background)', opacity: 0.22 }} />
          {[0, 1, 2].map(row => (
            <g key={row}>
              <rect className="offline-twinkle" x="72" y={106 + row * 22} width="9" height="12" rx="2" style={fill('--color-background')} />
              <rect className="offline-twinkle offline-twinkle--late" x="85" y={106 + row * 22} width="7" height="12" rx="2" style={fill('--color-background')} />
              <rect className="offline-twinkle offline-twinkle--late" x="148" y={114 + row * 20} width="9" height="12" rx="2" style={fill('--color-background')} />
              <rect className="offline-twinkle" x="161" y={114 + row * 20} width="7" height="12" rx="2" style={fill('--color-background')} />
            </g>
          ))}
          <path d="M106 152 v22 h28 v-22 a14 14 0 0 0 -28 0 z" style={fill('--color-text-primary')} />
          <circle cx="130" cy="164" r="1.8" style={fill('--color-gold')} />
          <circle className="offline-lamp" cx="120" cy="143" r="9" style={{ fill: 'var(--color-gold)', opacity: 0.3 }} />
          <circle cx="120" cy="143" r="3.6" style={fill('--color-gold')} />
          <path d="M91 56 Q104 14 144 28 Q130 33 142 53 Z" style={fill('--color-text-primary')} />
          <path d="M91 56 L149 54" style={{ stroke: 'var(--color-gold-dark)' }} strokeWidth="5" strokeLinecap="round" />
          <circle cx="146" cy="27" r="6" style={fill('--color-gold')} />
          <path d="M104 86 q8 8 16 0 M104 86 l-3 -2 M105.5 88.5 l-3.5 1.2" {...line} strokeWidth="3" strokeLinecap="round" />
          <path d="M126 86 q8 8 16 0 M142 86 l3 -2 M140.5 88.5 l3.5 1.2" {...line} strokeWidth="3" strokeLinecap="round" />
          <circle cx="101" cy="97" r="5" style={{ fill: 'var(--color-gold-dark)', opacity: 0.35 }} />
          <circle cx="145" cy="97" r="5" style={{ fill: 'var(--color-gold-dark)', opacity: 0.35 }} />
          <ellipse cx="123" cy="103" rx="3.4" ry="2.8" style={fill('--color-text-primary')} />
          <circle className="offline-bubble" cx="128" cy="105" r="6" style={{ fill: 'var(--color-background)', stroke: 'var(--color-text-primary)', opacity: 0.7 }} strokeWidth="1.4" />
        </g>
        <g className="offline-suitcase">
          <path d="M77 160 v-4 a3 3 0 0 1 3 -3 h6 a3 3 0 0 1 3 3 v4" {...line} strokeWidth="2" />
          <rect x="72" y="160" width="22" height="14" rx="3" style={fill('--color-text-primary')} />
          <rect x="80" y="164" width="6" height="5" rx="1.5" style={fill('--color-gold')} />
        </g>
      </g>
      <g style={{ fill: 'var(--color-text-secondary)' }} fontFamily="serif" fontWeight="700">
        <text className="offline-zzz" x="156" y="38" fontSize="14">z</text>
        <text className="offline-zzz offline-zzz--2" x="164" y="26" fontSize="19">z</text>
        <text className="offline-zzz offline-zzz--3" x="174" y="10" fontSize="25">Z</text>
      </g>
      <g transform="translate(46 44)">
        <g className="offline-pulse">
          <circle r="22" style={{ fill: 'var(--color-background-alt)', stroke: 'var(--color-border)' }} strokeWidth="2" />
          <path d="M-12 -2 a17 17 0 0 1 24 0 M-8 4 a11 11 0 0 1 16 0" {...line} strokeWidth="3" strokeLinecap="round" />
          <circle cx="0" cy="11" r="2.4" style={fill('--color-text-primary')} />
          <path d="M-14 -14 L14 14" style={{ stroke: 'var(--color-error)' }} strokeWidth="4" strokeLinecap="round" />
        </g>
      </g>
    </svg>
  )
}

/** Covers the app while the device has no internet; goes away by itself when it is back. */
export function OfflineScreen() {
  const { t } = useI18n()
  const { online, recheck } = useOnlineStatus()
  const [checking, setChecking] = useState(false)
  const [stillOffline, setStillOffline] = useState(false)
  const [jolt, setJolt] = useState(false)
  const joltTimer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(joltTimer.current), [])

  if (online) return null

  /** Touching the picture wakes the hotel up for a moment: it jumps, then falls asleep again */
  const wake = () => {
    window.clearTimeout(joltTimer.current)
    setJolt(true)
    joltTimer.current = window.setTimeout(() => setJolt(false), 700)
  }

  const retry = async () => {
    setChecking(true)
    setStillOffline(false)
    const reached = await recheck()
    setChecking(false)
    setStillOffline(!reached)
  }

  return (
    <div className="offline-screen" role="alert">
      <div className="offline-card">
        <div className={`offline-art-wrap${jolt ? ' offline-jolt' : ''}`} onClick={wake} role="presentation">
          <SleepingHotel />
        </div>
        <h2 className="offline-title">{t('offline.title')}</h2>
        <p className="offline-hint">{t('offline.hint')}</p>
        <button type="button" className="btn btn-primary" onClick={() => void retry()} disabled={checking}>
          {checking ? t('offline.checking') : t('offline.retry')}
        </button>
        {stillOffline && <p className="offline-still">{t('offline.still')}</p>}
      </div>
    </div>
  )
}
