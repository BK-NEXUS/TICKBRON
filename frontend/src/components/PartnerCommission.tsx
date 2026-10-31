import { useCallback, useEffect, useState } from 'react'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { CommissionStatement as Statement } from '../adapters/commissionTypes'
import { useI18n } from '../i18n/I18nContext'
import { CommissionStatement } from './CommissionStatement'

/** What the owner owes the site: the agreed percent, the commission of each month, and which months are confirmed as paid. */
export function PartnerCommission() {
  const { t } = useI18n()
  const [statement, setStatement] = useState<Statement | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    const result = await partnerAdapter.getCommission()
    if (result.data) setStatement(result.data)
    else setError(result.error ?? t('commission.loadError'))
    setLoading(false)
  }, [t])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="partner-commission">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('commission.ownerTitle')}</h2>
        <p className="admin-view-subtitle">{t('commission.ownerSubtitle')}</p>
      </div>
      {error && (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !statement && !error && <p className="loading-state" role="status">{t('commission.loading')}</p>}
      {statement && <CommissionStatement statement={statement} />}
    </div>
  )
}
