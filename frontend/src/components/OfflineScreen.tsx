import { useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { useOnlineStatus } from '../hooks/useOnlineStatus'

/** TICKBRON's own picture: the hotel in a night cap, asleep between two palms, and a "no signal" badge. Colours follow the theme. */
function SleepingHotel() {
  const fill = (color: string) => ({ fill: `var(${color})` })
  const line = { stroke: 'var(--color-text-primary)', fill: 'none' }
  const palm = (x: number, scale: number, extra: string) => (
    <g transform={`translate(${x} 170) scale(${scale})`}>
      <g className={`offline-sway ${extra}`}>
        <path d="M0 0 C -5 -28 5 -52 0 -78" style={{ stroke: 'var(--color-gold-dark)' }} strokeWidth="6" strokeLinecap="round" fill="none" />
        {[-168, -132, -96, -60, -24, 12, 148].map(angle => (
          <path key={angle} d="M0 0 C 12 -16 38 -16 56 6 C 38 -3 14 -2 0 0 Z" transform={`translate(0 -78) rotate(${angle})`}
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
    <svg className="offline-art" viewBox="0 0 240 200" width="240" height="200" aria-hidden="true" focusable="false">
      {cloud(190, 38, '')}
      {cloud(30, 92, 'offline-drift--slow')}
      <ellipse cx="120" cy="174" rx="98" ry="9" style={fill('--color-border')} />
      {palm(42, 0.95, '')}
      {palm(198, 0.78, 'offline-sway--slow')}
      <g className="offline-breathe">
        <rect x="66" y="94" width="32" height="80" rx="5" style={fill('--color-gold-dark')} />
        <rect x="142" y="104" width="32" height="70" rx="5" style={fill('--color-gold-dark')} />
        <rect x="92" y="52" width="56" height="122" rx="9" style={fill('--color-gold')} />
        {[0, 1, 2].map(row => (
          <g key={row}>
            <rect className="offline-twinkle" x="72" y={106 + row * 22} width="9" height="12" rx="2" style={fill('--color-background')} />
            <rect className="offline-twinkle offline-twinkle--late" x="85" y={106 + row * 22} width="7" height="12" rx="2" style={fill('--color-background')} />
            <rect className="offline-twinkle offline-twinkle--late" x="148" y={114 + row * 20} width="9" height="12" rx="2" style={fill('--color-background')} />
            <rect className="offline-twinkle" x="161" y={114 + row * 20} width="7" height="12" rx="2" style={fill('--color-background')} />
          </g>
        ))}
        <path d="M106 152 v22 h28 v-22 a14 14 0 0 0 -28 0 z" style={fill('--color-text-primary')} />
        <circle cx="132" cy="165" r="1.8" style={fill('--color-gold')} />
        <path d="M91 56 Q104 14 144 28 Q130 33 142 53 Z" style={fill('--color-text-primary')} />
        <path d="M91 56 L149 54" style={{ stroke: 'var(--color-gold-dark)' }} strokeWidth="5" strokeLinecap="round" />
        <circle cx="146" cy="27" r="6" style={fill('--color-gold')} />
        <path d="M104 86 q8 8 16 0" {...line} strokeWidth="3.2" strokeLinecap="round" />
        <path d="M126 86 q8 8 16 0" {...line} strokeWidth="3.2" strokeLinecap="round" />
        <circle cx="101" cy="96" r="4.5" style={{ fill: 'var(--color-gold-dark)', opacity: 0.35 }} />
        <circle cx="145" cy="96" r="4.5" style={{ fill: 'var(--color-gold-dark)', opacity: 0.35 }} />
        <ellipse cx="123" cy="103" rx="4" ry="3.2" style={fill('--color-text-primary')} />
      </g>
      <g style={{ fill: 'var(--color-text-secondary)' }} fontFamily="serif" fontWeight="700">
        <text className="offline-zzz" x="156" y="46" fontSize="14">z</text>
        <text className="offline-zzz offline-zzz--2" x="164" y="34" fontSize="19">z</text>
        <text className="offline-zzz offline-zzz--3" x="174" y="20" fontSize="25">Z</text>
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

  if (online) return null

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
        <SleepingHotel />
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
