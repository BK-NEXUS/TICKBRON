import { cleanPlaceName } from '../utils/inputFilters'
import { FormEvent, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { adminGeographyAdapter, type AdminGeographyRow, type GeographyKind } from '../adapters/adminGeographyAdapter'
import { DialogModal } from './DialogModal'

const NAME_FIELDS = ['name_uz', 'name_ru', 'name_en'] as const

interface GeographyRowDialogProps {
  kind: GeographyKind
  /** The open country (for a region) or region (for a city); null for a country */
  parentId: number | null
  /** The row being edited; absent when adding */
  row?: AdminGeographyRow
  onSaved: () => void
  onClose: () => void
}

/** Add or edit one country, region or city. The code, currency and parent are set only when adding. */
export function GeographyRowDialog({ kind, parentId, row, onSaved, onClose }: GeographyRowDialogProps) {
  const { t } = useI18n()
  const id = useId()
  const [names, setNames] = useState({
    name_uz: row?.name_uz ?? '', name_ru: row?.name_ru ?? '', name_en: row?.name_en ?? '',
  })
  const [code, setCode] = useState('')
  const [currency, setCurrency] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parentField = kind === 'regions' ? { country: parentId as number } : kind === 'cities' ? { region: parentId as number } : {}
  const createBody = kind === 'countries' ? { code, currency, ...names } : { ...parentField, ...names }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    const result = row
      ? await adminGeographyAdapter.update(kind, row.id, names)
      : await adminGeographyAdapter.create(kind, createBody)
    setSaving(false)
    if (result.error) {
      setError(result.error)
      return
    }
    onSaved()
  }

  const title = t(row ? `geoAdmin.edit.${kind}` : `geoAdmin.new.${kind}`)

  return (
    <DialogModal titleId={`${id}-title`} title={title} onClose={onClose}>
      <form onSubmit={handleSubmit} className="geography-row-form">
        {!row && kind === 'countries' && (
          <>
            <div className="form-group">
              <label htmlFor={`${id}-code`}>{t('geoAdmin.field.code')}</label>
              <input id={`${id}-code`} className="form-input" maxLength={2} required value={code}
                onChange={e => setCode(e.target.value.replace(/[^a-zA-Z]/g, ''))} />
            </div>
            <div className="form-group">
              <label htmlFor={`${id}-currency`}>{t('geoAdmin.field.currency')}</label>
              <input id={`${id}-currency`} className="form-input" maxLength={3} required value={currency}
                onChange={e => setCurrency(e.target.value.replace(/[^a-zA-Z]/g, ''))} />
            </div>
          </>
        )}
        {NAME_FIELDS.map(field => (
          <div className="form-group" key={field}>
            <label htmlFor={`${id}-${field}`}>{t(`geoAdmin.field.${field}`)}</label>
            <input id={`${id}-${field}`} className="form-input" maxLength={100} required value={names[field]}
              onChange={e => setNames(prev => ({ ...prev, [field]: cleanPlaceName(e.target.value) }))} />
          </div>
        ))}
        {error && <p role="alert" className="geography-picker-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>{t('geoAdmin.cancel')}</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? t('geoAdmin.saving') : t('geoAdmin.save')}
          </button>
        </div>
      </form>
    </DialogModal>
  )
}
