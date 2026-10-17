import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import {
  EXCHANGE_RATE_PAGE_SIZE,
  exchangeRateAdapter,
  type CurrencyRateStatus,
  type ExchangeRateRow,
  type ExchangeRateStatus,
} from '../adapters/exchangeRateAdapter'
import type { Paginated } from '../utils/api'
import { DialogModal } from './DialogModal'
import { StatusPagination } from './StatusPagination'

interface AdminExchangeRatesProps {
  /** The fetch status and accepting a rejected rate are for the super-admin; the backend enforces it too. */
  isSuperAdmin: boolean
}

const LOCALES = { uz: 'uz', ru: 'ru', en: 'en' } as const

/** Admin: the CBU rates the guests are charged at, their history, and what needs a decision. */
export function AdminExchangeRates({ isSuperAdmin }: AdminExchangeRatesProps) {
  const { t, tp, language, formatDate } = useI18n()
  const [page, setPage] = useState(1)
  const [history, setHistory] = useState<Paginated<ExchangeRateRow> | null>(null)
  const [status, setStatus] = useState<ExchangeRateStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [toAccept, setToAccept] = useState<ExchangeRateRow | null>(null)
  const [accepting, setAccepting] = useState(false)
  const [acceptError, setAcceptError] = useState<string | null>(null)

  const formatRate = (rate: string) =>
    Number(rate).toLocaleString(LOCALES[language], { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  // Doubles as the Try Again button and the refresh after accepting a rate
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const [rates, current] = await Promise.all([
      exchangeRateAdapter.list({ page }),
      isSuperAdmin ? exchangeRateAdapter.status() : Promise.resolve(null),
    ])
    if (rates.data && (!current || current.data)) {
      setHistory(rates.data)
      setStatus(current?.data ?? null)
    } else {
      setLoadFailed(true)
    }
    setLoading(false)
  }, [page, isSuperAdmin])

  useEffect(() => {
    void load()
  }, [load])

  const confirmAccept = async () => {
    if (!toAccept) return
    setAccepting(true)
    setAcceptError(null)
    const result = await exchangeRateAdapter.accept(toAccept.id)
    setAccepting(false)
    if (result.error) {
      setAcceptError(result.error)
      return
    }
    setToAccept(null)
    await load()
  }

  const rejectedCount = status?.currencies.reduce((sum, c) => sum + c.rejected.length, 0) ?? 0

  const renderCurrency = (currency: CurrencyRateStatus) => (
    <div className="fx-rate-card" key={currency.currency}>
      {currency.rate && currency.date ? (
        <>
          <p className="fx-rate-card-rate">{t('fxAdmin.rateLine', { currency: currency.currency, rate: formatRate(currency.rate) })}</p>
          <small>{t('fxAdmin.rateOf', { date: formatDate(currency.date), source: currency.source ?? '' })}</small>
        </>
      ) : (
        <p className="fx-rate-card-rate">{t('fxAdmin.noRate')}</p>
      )}
      {currency.rate && currency.stale && (
        <p role="alert" className="alert alert-error">{t('fxAdmin.warnStale', { currency: currency.currency })}</p>
      )}
      {currency.last_error && <small>{t('fxAdmin.lastError', { error: currency.last_error })}</small>}
    </div>
  )

  return (
    <div className="admin-exchange-rates">
      <h2 className="admin-view-title">{t('fxAdmin.title')}</h2>
      <p className="admin-view-subtitle">{t('fxAdmin.subtitle')}</p>
      {!isSuperAdmin && <p className="admin-view-subtitle">{t('fxAdmin.readOnly')}</p>}

      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('fxAdmin.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !history && !loadFailed && <p className="loading-state">{t('fxAdmin.loading')}</p>}

      {status && (
        <section>
          <h3 className="admin-section-title">{t('fxAdmin.currentTitle')}</h3>
          {status.currencies.map(renderCurrency)}
          {rejectedCount > 0 && (
            <p role="alert" className="alert alert-error">{tp('fxAdmin.warnRejected', rejectedCount)}</p>
          )}
          {rejectedCount > 0 && (
            <div>
              <h3 className="admin-section-title">{t('fxAdmin.rejectedTitle')}</h3>
              <table className="customers-table">
                <tbody>
                  {status.currencies.flatMap(currency => currency.rejected).map(rejected => (
                    <tr key={rejected.id}>
                      <td>{formatDate(rejected.rate_date)}</td>
                      <td>{rejected.currency}</td>
                      <td>{formatRate(rejected.rate)}</td>
                      <td>{rejected.note}</td>
                      <td>
                        <button type="button" className="btn btn-secondary btn-sm"
                          aria-label={t('fxAdmin.acceptRow', { currency: rejected.currency, date: formatDate(rejected.rate_date) })}
                          onClick={() => { setAcceptError(null); setToAccept(rejected) }}>
                          {t('fxAdmin.accept')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {history && (
        <section>
          <h3 className="admin-section-title">{t('fxAdmin.historyTitle')}</h3>
          {history.results.length === 0 ? (
            <p className="empty-state">{t('fxAdmin.empty')}</p>
          ) : (
            <div className="customers-table-container table-scroll">
              <table className="customers-table">
                <thead>
                  <tr>
                    <th>{t('fxAdmin.col.date')}</th>
                    <th>{t('fxAdmin.col.currency')}</th>
                    <th>{t('fxAdmin.col.rate')}</th>
                    <th>{t('fxAdmin.col.source')}</th>
                    <th>{t('fxAdmin.col.status')}</th>
                    <th>{t('fxAdmin.col.note')}</th>
                  </tr>
                </thead>
                <tbody>
                  {history.results.map(item => (
                    <tr key={item.id}>
                      <td>{formatDate(item.rate_date)}</td>
                      <td>{item.currency}</td>
                      <td>{formatRate(item.rate)}</td>
                      <td>{item.source}</td>
                      <td>
                        <span className={`status-badge status-badge--${item.status === 'accepted' ? 'active' : 'cancelled'}`}>
                          {t(`fxAdmin.status.${item.status}`)}
                        </span>
                      </td>
                      <td>{item.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {history.count > EXCHANGE_RATE_PAGE_SIZE && (
            <StatusPagination page={page} count={history.count} pageSize={EXCHANGE_RATE_PAGE_SIZE}
              hasPrevious={page > 1} hasNext={Boolean(history.next)} onPage={setPage} />
          )}
        </section>
      )}

      {toAccept && (
        <DialogModal titleId="fx-accept-title" title={t('fxAdmin.acceptTitle')} onClose={() => setToAccept(null)}>
          <p>{t('fxAdmin.acceptConfirm', { currency: toAccept.currency, rate: formatRate(toAccept.rate), date: formatDate(toAccept.rate_date) })}</p>
          {acceptError && <p role="alert" className="geography-picker-error">{acceptError}</p>}
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setToAccept(null)}>{t('fxAdmin.cancel')}</button>
            <button type="button" className="btn btn-primary" disabled={accepting} onClick={() => void confirmAccept()}>{t('fxAdmin.accept')}</button>
          </div>
        </DialogModal>
      )}
    </div>
  )
}
