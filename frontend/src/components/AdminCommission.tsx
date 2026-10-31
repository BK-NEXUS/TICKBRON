import { useCallback, useEffect, useState } from 'react'
import { adminAdapter, type ApiResponse } from '../adapters/adminAdapter'
import type { CommissionOwnerPage, CommissionOwnerRow, CommissionStatement as Statement, MoneyLine } from '../adapters/commissionTypes'
import { useI18n } from '../i18n/I18nContext'
import { CommissionStatement } from './CommissionStatement'
import { StatusPagination } from './StatusPagination'

const PAGE_SIZE = 20
const SEARCH_DELAY_MS = 300
const PERCENT_FORMAT = /^\d{1,3}(\.\d{1,2})?$/

interface AdminCommissionProps {
  /** Only a super admin sets the percent; staff confirm payments. The backend enforces both. */
  isSuperAdmin: boolean
}

function isPercent(text: string): boolean {
  return PERCENT_FORMAT.test(text) && Number(text) <= 100
}

/** The super admin's and staff's Commission section: every hotel owner, a search, and one owner's months. */
export function AdminCommission({ isSuperAdmin }: AdminCommissionProps) {
  const { t, formatMoney } = useI18n()
  const [typed, setTyped] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [list, setList] = useState<CommissionOwnerPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selected, setSelected] = useState<CommissionOwnerRow | null>(null)
  const [statement, setStatement] = useState<Statement | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [busyMonth, setBusyMonth] = useState<string | null>(null)
  const [percentText, setPercentText] = useState('')
  const [percentError, setPercentError] = useState<string | null>(null)
  const [percentSaved, setPercentSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => { setSearch(typed.trim()); setPage(1) }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [typed])

  // Doubles as the Try Again button
  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    const result = await adminAdapter.getCommissionOwners({ search, page })
    if (result.data) setList(result.data)
    else setLoadError(result.error ?? t('commission.loadError'))
    setLoading(false)
  }, [search, page, t])

  useEffect(() => {
    void load()
  }, [load])

  const open = async (owner: CommissionOwnerRow) => {
    setSelected(owner)
    setStatement(null)
    setDetailError(null)
    setPercentError(null)
    setPercentSaved(false)
    const result = await adminAdapter.getCommissionStatement(owner.id)
    if (result.data) {
      setStatement(result.data)
      setPercentText(result.data.percent ?? '')
    } else setDetailError(result.error ?? t('commission.loadError'))
  }

  const close = () => {
    setSelected(null)
    void load()
  }

  const apply = async (action: () => Promise<ApiResponse<Statement>>, month: string | null = null) => {
    setBusyMonth(month)
    setDetailError(null)
    const result = await action()
    setBusyMonth(null)
    if (result.data) setStatement(result.data)
    else setDetailError(result.error ?? t('commission.loadError'))
    return result
  }

  const savePercent = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!selected) return
    setPercentSaved(false)
    if (!isPercent(percentText.trim())) {
      setPercentError(t('commission.percentInvalid'))
      return
    }
    setPercentError(null)
    setSaving(true)
    const result = await apply(() => adminAdapter.setCommissionPercent(selected.id, percentText.trim()))
    setSaving(false)
    if (result.data) setPercentSaved(true)
  }

  const money = (lines: MoneyLine[] | null) => {
    if (lines === null) return t('commission.notSet')
    if (lines.length === 0) return t('commission.none')
    return lines.map(line => formatMoney(line.amount, line.currency, { minDecimals: 2, maxDecimals: 2 })).join(', ')
  }

  if (selected) {
    return (
      <div className="admin-commission">
        <button type="button" className="btn btn-secondary btn-sm" onClick={close}>{t('commission.back')}</button>
        <div className="admin-view-header">
          <h2 className="admin-view-title">{selected.name}</h2>
          <p className="admin-view-subtitle">
            {selected.email}{selected.phone_number ? ` · ${selected.phone_number}` : ''}
          </p>
        </div>
        {detailError && <p className="alert alert-error" role="alert">{detailError}</p>}
        {!statement && !detailError && <p className="loading-state" role="status">{t('commission.loading')}</p>}
        {statement && isSuperAdmin && (
          <form className="commission-percent-form" onSubmit={savePercent} noValidate>
            <label htmlFor="commission-percent">{t('commission.setPercent')}</label>
            <input id="commission-percent" className="search-input" inputMode="decimal" autoComplete="off"
              value={percentText} disabled={saving} aria-describedby="commission-percent-hint"
              onChange={(e) => { setPercentText(e.target.value); setPercentSaved(false) }} />
            <small id="commission-percent-hint" className="form-hint">{t('commission.percentHint')}</small>
            {percentError && <p className="alert alert-error" role="alert">{percentError}</p>}
            {percentSaved && <p className="alert alert-success" role="status">{t('commission.percentSaved')}</p>}
            <button type="submit" className="btn btn-primary btn-sm" disabled={saving}>{t('commission.save')}</button>
          </form>
        )}
        {statement && (
          <CommissionStatement statement={statement} confirmation={{
            busyMonth,
            onConfirm: month => void apply(() => adminAdapter.confirmCommissionMonth(selected.id, month), month),
            onUndo: month => void apply(() => adminAdapter.undoCommissionMonth(selected.id, month), month),
          }} />
        )}
      </div>
    )
  }

  const rows = list?.results ?? []

  return (
    <div className="admin-commission">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('commission.title')}</h2>
        <p className="admin-view-subtitle">{t('commission.subtitle')}</p>
      </div>

      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="commission-search" className="search-label">{t('commission.searchLabel')}</label>
          <input id="commission-search" type="search" className="search-input" value={typed}
            maxLength={100} placeholder={t('commission.searchPlaceholder')}
            onChange={(e) => setTyped(e.target.value)} />
        </div>
      </div>

      {loadError && (
        <div className="alert alert-error" role="alert">
          <p>{loadError}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !list && !loadError && <p className="loading-state" role="status">{t('commission.loading')}</p>}
      {!loading && !loadError && rows.length === 0 && <p className="empty-state">{t('commission.empty')}</p>}

      {rows.length > 0 && (
        <ul className="renewal-list">
          {rows.map(owner => (
            <li key={owner.id} className="renewal-card">
              <div className="renewal-card-head">
                <div>
                  <strong>{owner.name}</strong>
                  <div className="promotion-city">{owner.email}{owner.phone_number ? ` · ${owner.phone_number}` : ''}</div>
                </div>
                <span className="status-badge status-badge--pending">
                  {owner.percent === null ? t('commission.notSet') : `${owner.percent}%`}
                </span>
              </div>
              <dl className="renewal-facts">
                <div>
                  <dt>{t('commission.thisMonth')}</dt>
                  <dd>{money(owner.this_month.commission)}</dd>
                </div>
                <div>
                  <dt>{t('commission.unpaid')}</dt>
                  <dd>{money(owner.unpaid)}</dd>
                </div>
              </dl>
              <div className="promotion-actions">
                <button type="button" className="btn btn-primary btn-sm"
                  aria-label={`${t('commission.open')}: ${owner.name}`} onClick={() => void open(owner)}>
                  {t('commission.open')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {list && list.count > PAGE_SIZE && (
        <StatusPagination page={page} count={list.count} pageSize={PAGE_SIZE}
          hasPrevious={page > 1} hasNext={list.hasMore} onPage={setPage} />
      )}
    </div>
  )
}
