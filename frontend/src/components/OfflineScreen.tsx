import { useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { useOnlineStatus } from '../hooks/useOnlineStatus'

/** TICKBRON's own picture: the hotel with its two palms, asleep, and a "no signal" badge. Colours follow the theme. */
function SleepingHotel() {
  const gold = { fill: 'var(--color-gold)' }
  const goldDark = { fill: 'var(--color-gold-dark)' }
  const ink = { stroke: 'var(--color-text-primary)', fill: 'none' }
  const palm = (x: number, scale: number) => (
    <g transform={`translate(${x} 160) scale(${scale})`}>
      <path d="M0 0 C -4 -30 4 -55 0 -80" style={{ stroke: 'var(--color-gold-dark)' }} strokeWidth="6" strokeLinecap="round" fill="none" />
      {[-42, -22, 0, 22, 42].map(angle => (
        <path key={angle} d="M0 -80 C 14 -96 34 -92 44 -76" transform={`rotate(${angle} 0 -80)`}
          style={{ stroke: 'var(--color-gold)' }} strokeWidth="7" strokeLinecap="round" fill="none" />
      ))}
    </g>
  )
  return (
    <svg className="offline-art" viewBox="0 0 240 200" width="240" height="200" aria-hidden="true" focusable="false">
      <ellipse cx="120" cy="172" rx="96" ry="9" style={{ fill: 'var(--color-border)' }} />
      {palm(44, 0.9)}
      {palm(196, 0.75)}
      <rect x="68" y="92" width="30" height="80" rx="5" style={goldDark} />
      <rect x="142" y="102" width="30" height="70" rx="5" style={goldDark} />
      <rect x="92" y="44" width="56" height="128" rx="8" style={gold} />
      {[0, 1].map(row => (
        <g key={row}>
          <rect x="74" y={104 + row * 24} width="8" height="12" rx="2" style={{ fill: 'var(--color-background)' }} />
          <rect x="86" y={104 + row * 24} width="6" height="12" rx="2" style={{ fill: 'var(--color-background)' }} />
          <rect x="148" y={114 + row * 24} width="8" height="12" rx="2" style={{ fill: 'var(--color-background)' }} />
          <rect x="160" y={114 + row * 24} width="6" height="12" rx="2" style={{ fill: 'var(--color-background)' }} />
        </g>
      ))}
      <path d="M106 150 v22 h28 v-22 a14 14 0 0 0 -28 0 z" style={{ fill: 'var(--color-text-primary)' }} />
      <path d="M104 78 q8 8 16 0" {...ink} strokeWidth="3.2" strokeLinecap="round" />
      <path d="M126 78 q8 8 16 0" {...ink} strokeWidth="3.2" strokeLinecap="round" />
      <path d="M114 96 q6 5 12 0" {...ink} strokeWidth="3" strokeLinecap="round" />
      <g className="offline-art-z" style={{ fill: 'var(--color-text-secondary)' }} fontFamily="serif" fontWeight="700">
        <text x="150" y="52" fontSize="16">z</text>
        <text x="162" y="38" fontSize="22">Z</text>
      </g>
      <g transform="translate(46 44)">
        <circle r="22" style={{ fill: 'var(--color-background-alt)', stroke: 'var(--color-border)' }} strokeWidth="2" />
        <path d="M-12 -2 a17 17 0 0 1 24 0 M-8 4 a11 11 0 0 1 16 0" {...ink} strokeWidth="3" strokeLinecap="round" />
        <circle cx="0" cy="11" r="2.4" style={{ fill: 'var(--color-text-primary)' }} />
        <path d="M-14 -14 L14 14" style={{ stroke: 'var(--color-error)' }} strokeWidth="4" strokeLinecap="round" />
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
