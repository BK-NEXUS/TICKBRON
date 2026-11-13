import { AlphabetFilter } from './AlphabetFilter'
import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { ReactNode, useEffect, useId, useState } from 'react'
import type { StatusListParams, StatusPage, StatusResponse } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { formatCount } from '../utils/statusFormat'
import { StatusPagination } from './StatusPagination'
import type { DateRange } from '../utils/statusPeriod'

const SEARCH_DELAY_MS = 300

export interface StatusColumn<T> {
  header: string
  render: (row: T) => ReactNode
  numeric?: boolean
}

interface StatusRankedTableProps<T> {
  title: string
  subtitle?: string
  /** mısalı "mámleketler": izlew belgisinde hám bos xabarda paydalanıladı */
  noun: string
  period: string
  onPeriodChange: (period: string) => void
  /** Qollanılǵan custom aralıq; `onRangeChange` penen tańlaǵısh custom variantın usınadı */
  range?: DateRange | null
  onRangeChange?: (range: DateRange) => void
  /** Izlew qutısı janındaǵı qosımsha basqarıwlar, mısalı tártiplew */
  toolbar?: ReactNode
  /** Házirgi izlewdi talap etetuǵın qosımsha háreketler, mısalı eksport túymesi */
  renderActions?: (state: { search: string; letter: string }) => ReactNode
  /** Alfavit filterin kórsetiw: tek endpoint i ?letter= qabıllaytuǵın dizimler ushın (mehmanxanalar hám mehmanlar) */
  alphabet?: boolean
  /** Onı ózgertiw dizimdi birinshi betten qayta júkleydi (`load` jawıp turǵan variantlar ushın paydalanıń) */
  reloadKey?: string
  load: (params: StatusListParams) => Promise<StatusResponse<StatusPage<T>>>
  rowKey: (row: T) => string | number
  /** Qatardıń silteme túymesiniń teksti (birinshi baǵana) */
  rowLabel: (row: T) => string
  onOpen: (row: T) => void
  columns: StatusColumn<T>[]
}

/**
 * Óz izlew qutısı (tek usı dizimdi izleydi) hám ortaq dáwir tańlaǵıshı menen bir ráteli, betlerge bólingen Status dizimi.
 * Júklew, bos hám qátelik jaǵdayları kiredi.
 */
export function StatusRankedTable<T>({
  title, subtitle, noun, period, onPeriodChange, range, onRangeChange, toolbar, renderActions, alphabet = false, reloadKey = '',
  load, rowKey, rowLabel, onOpen, columns,
}: StatusRankedTableProps<T>) {
  const { t } = useI18n()
  // `noun` xabar kilti (yamasa ápiwayı sóz, ol ózgerissiz qaytadı)
  const nounText = t(noun as MessageKey)
  const id = useId()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [letter, setLetter] = useState('')
  const [pageState, setPageState] = useState({ key: reloadKey, page: 1 })
  // Jańa reloadKey ekinshi sorawsız birinshi betten qayta baslanadı
  const page = pageState.key === reloadKey ? pageState.page : 1
  const goToPage = (next: number) => setPageState({ key: reloadKey, page: next })
  const [data, setData] = useState<StatusPage<T> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Paydalanıwshı teriwdi toqtatqannan keyin, birinshi betten izlew
  useEffect(() => {
    if (searchInput === search) return
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setPageState(state => ({ ...state, page: 1 }))
    }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchInput, search])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    const applied = period === 'custom' && range ? { from: range.from, to: range.to } : {}
    load({ period, ...applied, search, letter: letter || undefined, page }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
    // `load` hár render de jańa funkciya; dizim neni soraǵanına baylanıslı
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, range, search, letter, page, reloadKey])

  const handlePeriod = (next: string) => {
    goToPage(1)
    onPeriodChange(next)
  }

  const handleRange = (next: DateRange) => {
    goToPage(1)
    onRangeChange?.(next)
  }

  const rows = data?.results ?? []

  return (
    <section className="status-list" aria-labelledby={`${id}-title`}>
      <div className="admin-view-header">
        <h2 id={`${id}-title`} className="admin-view-title">{title}</h2>
        {subtitle && <p className="admin-view-subtitle">{subtitle}</p>}
      </div>

      <div className="status-controls">
        <div className="status-search">
          <label htmlFor={`${id}-search`} className="sr-only">{t('status.searchNoun', { noun: nounText })}</label>
          <input
            id={`${id}-search`}
            type="search"
            className="search-input"
            placeholder={t('status.searchNounPlaceholder', { noun: nounText })}
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
          />
        </div>
        {toolbar}
        <StatusPeriodSelector
          value={period} range={range} onChange={handlePeriod} onRangeChange={onRangeChange && handleRange}
        />
        {renderActions?.({ search, letter })}
      </div>
      {alphabet && <AlphabetFilter value={letter} onChange={next => { setLetter(next); goToPage(1) }} />}

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : loading ? (
        <div className="loading-state" role="status" aria-live="polite">{t('status.loadingNoun', { noun: nounText })}</div>
      ) : rows.length === 0 ? (
        <div className="empty-state">
          <p>{search ? t('status.noMatch', { noun: nounText, search }) : t('status.noneForPeriod', { noun: nounText })}</p>
        </div>
      ) : (
        <>
          <div className="customers-table-container">
            <table className="customers-table status-table">
              <thead>
                <tr>
                  <th scope="col" className="status-cell--numeric">#</th>
                  {columns.map(column => (
                    <th key={column.header} scope="col" className={column.numeric ? 'status-cell--numeric' : undefined}>
                      {column.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr key={rowKey(row)} className="status-row" onClick={() => onOpen(row)}>
                    <td className="status-cell--numeric">{formatCount((row as { rank: number }).rank)}</td>
                    {columns.map((column, index) => (
                      <td key={column.header} className={column.numeric ? 'status-cell--numeric' : undefined}>
                        {index === 0 ? (
                          <button
                            type="button"
                            className="status-row-link"
                            onClick={event => { event.stopPropagation(); onOpen(row) }}
                          >
                            {rowLabel(row)}
                          </button>
                        ) : column.render(row)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <StatusPagination
            page={page} count={data?.count ?? 0} hasPrevious={Boolean(data?.previous)} hasNext={Boolean(data?.next)}
            onPage={goToPage}
          />
        </>
      )}
    </section>
  )
}
