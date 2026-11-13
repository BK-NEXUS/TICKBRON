import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'

export interface Crumb {
  label: string
  /** Crumb qayaqqa alıp baradı; aqırǵı crumb (házirgi bet) ta joq */
  to?: string
  /** Bet ishindegi dárejesi (mısalı partner dashboard kórinisi): silteme ornına túyme */
  onClick?: () => void
}

interface TrailEntry {
  labelKey: MessageKey
  to?: string
}

/** Bet óz izin belgilemese, hár route ushın ádetdegi iz (Bas bet ten keyin) */
const ROUTE_TRAILS: Array<[RegExp, TrailEntry[]]> = [
  [/^\/login$/, [{ labelKey: 'auth.signIn' }]],
  [/^\/register$/, [{ labelKey: 'auth.createAccount' }]],
  [/^\/forgot-password$/, [{ labelKey: 'auth.forgotTitle' }]],
  [/^\/reset-password$/, [{ labelKey: 'auth.resetTitle' }]],
  [/^\/bookings$/, [{ labelKey: 'header.myBookings' }]],
  [/^\/booking$/, [{ labelKey: 'crumb.booking' }]],
  [/^\/favorites$/, [{ labelKey: 'crumb.myFavorites' }]],
  [/^\/support$/, [{ labelKey: 'chat.open' }]],
  [/^\/profile$/, [{ labelKey: 'crumb.profile' }]],
  [/^\/partner$/, [{ labelKey: 'header.partnerDashboard' }]],
  [/^\/admin$/, [{ labelKey: 'header.adminDashboard' }]],
  [/^\/admin\/support$/, [{ labelKey: 'header.adminDashboard', to: '/admin' }, { labelKey: 'crumb.supportLookup' }]],
  [/^\/admin\/customers\/\d+$/, [{ labelKey: 'header.adminDashboard', to: '/admin' }, { labelKey: 'crumb.customer' }]],
  [/^\/property\/\d+$/, [{ labelKey: 'nav.properties', to: '/search' }, { labelKey: 'crumb.property' }]],
  [/^\/destinations$/, [{ labelKey: 'footer.destinations' }]],
  [/^\/about$/, [{ labelKey: 'nav.about' }]],
  [/^\/help$/, [{ labelKey: 'footer.helpCenter' }]],
  [/^\/contact$/, [{ labelKey: 'footer.contact' }]],
  [/^\/safety$/, [{ labelKey: 'footer.safety' }]],
  [/^\/terms$/, [{ labelKey: 'footer.terms' }]],
  [/^\/privacy$/, [{ labelKey: 'footer.privacy' }]],
  [/^\/cookies$/, [{ labelKey: 'footer.cookies' }]],
]

function defaultTrail(pathname: string, search: string, t: (key: MessageKey) => string): Crumb[] {
  if (pathname === '/search') {
    const destination = new URLSearchParams(search).get('destination')
    return [{ label: destination || t('crumb.allProperties') }]
  }
  const match = ROUTE_TRAILS.find(([pattern]) => pattern.test(pathname))
  const entries: TrailEntry[] = match ? match[1] : [{ labelKey: 'crumb.notFound' }]
  return entries.map(({ labelKey, to }) => ({ label: t(labelKey), ...(to ? { to } : {}) }))
}

interface BreadcrumbContextValue {
  trail: Crumb[] | null
  setTrail: (trail: Crumb[] | null) => void
}

const BreadcrumbContext = createContext<BreadcrumbContextValue>({ trail: null, setTrail: () => {} })

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [trail, setTrail] = useState<Crumb[] | null>(null)
  const value = useMemo(() => ({ trail, setTrail }), [trail])
  return <BreadcrumbContext.Provider value={value}>{children}</BreadcrumbContext.Provider>
}

/**
 * Házirgi betke Bas bet ten keyin óz izin beriw, mısalı [{ label: 'Tashkent', to }, { label: 'Hotel' }].
 * Maǵlıwmat júklenip atırǵanda null beriń (sol waqıtta route tiń ádetdegi izi kórinedi).
 */
export function usePageTrail(trail: Crumb[] | null) {
  const { setTrail } = useContext(BreadcrumbContext)
  // Belgiler hám silteme ler izdiń ózgergenin sheshedi (onClick handler ler hár render de jańa funkciya)
  const key = JSON.stringify(trail?.map(crumb => [crumb.label, crumb.to ?? null, !!crumb.onClick]) ?? null)
  const latest = useRef(trail)
  latest.current = trail
  useEffect(() => {
    // Klikler belgiler eń sońǵı ózgergen waqıttaǵı emes, eń sońǵı render degi handler di shaqıradı
    setTrail(latest.current?.map((crumb, index) =>
      crumb.onClick ? { ...crumb, onClick: () => latest.current?.[index]?.onClick?.() } : crumb
    ) ?? null)
  }, [key, setTrail])
  useEffect(() => () => setTrail(null), [setTrail])
}

/** Bas bet ten basqa hár bette Artqa túymesi hám "Bas bet › ... › Házirgi bet" */
export function Breadcrumbs() {
  const location = useLocation()
  const navigate = useNavigate()
  const { trail: pageTrail } = useContext(BreadcrumbContext)
  const { t } = useI18n()

  if (location.pathname === '/') return null

  const trail = pageTrail ?? defaultTrail(location.pathname, location.search, t)
  const crumbs: Crumb[] = [{ label: t('crumb.home'), to: '/' }, ...trail]

  const handleBack = () => {
    // Óz dárejeleri bar bet ishinde Artqa aldın bir dárejege joqarı shıǵadı
    const parentCrumb = crumbs[crumbs.length - 2]
    if (parentCrumb?.onClick) {
      parentCrumb.onClick()
      return
    }
    // Ilova ashılǵan birinshi bet "default" kiltine iye: ilova ishinde qaytatuǵın hesh nárse joq
    if (location.key !== 'default') {
      navigate(-1)
      return
    }
    const parent = [...crumbs.slice(0, -1)].reverse().find(crumb => crumb.to)
    navigate(parent?.to ?? '/')
  }

  return (
    <div className="page-breadcrumbs container">
      <button type="button" className="btn btn-secondary page-breadcrumbs-back" onClick={handleBack} aria-label={t('crumb.back')}>
        <span className="page-breadcrumbs-back-arrow" aria-hidden="true">←</span> {t('crumb.back')}
      </button>
      <nav aria-label={t('crumb.trail')}>
        <ol className="page-breadcrumbs-list">
          {crumbs.map((crumb, index) => {
            const isCurrent = index === crumbs.length - 1
            return (
              <li key={`${index}-${crumb.label}`} className="page-breadcrumbs-item">
                {index > 0 && <span className="page-breadcrumbs-separator" aria-hidden="true">›</span>}
                {isCurrent || (!crumb.to && !crumb.onClick) ? (
                  <span aria-current={isCurrent ? 'page' : undefined}>{crumb.label}</span>
                ) : crumb.onClick ? (
                  <button type="button" className="page-breadcrumbs-link" onClick={crumb.onClick}>{crumb.label}</button>
                ) : (
                  <Link to={crumb.to!}>{crumb.label}</Link>
                )}
              </li>
            )
          })}
        </ol>
      </nav>
    </div>
  )
}
