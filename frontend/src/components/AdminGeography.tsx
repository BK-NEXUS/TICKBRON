import { useCallback, useEffect, useState } from 'react'
import { ArrowDown, ArrowUp } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import {
  adminGeographyAdapter,
  type AdminCountry,
  type AdminGeographyRow,
  type AdminRegion,
  type GeographyKind,
} from '../adapters/adminGeographyAdapter'
import { geographyName } from '../adapters/geographyAdapter'
import { DialogModal } from './DialogModal'
import { GeographyRowDialog } from './GeographyRowDialog'

const SEARCH_DELAY_MS = 300

/** Super-admin: the Country > Region > City dictionary (hide, rename, reorder, add, delete when unused). */
export function AdminGeography() {
  const { t, language } = useI18n()
  const [country, setCountry] = useState<AdminCountry | null>(null)
  const [region, setRegion] = useState<AdminRegion | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [rows, setRows] = useState<AdminGeographyRow[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [dialog, setDialog] = useState<{ row?: AdminGeographyRow } | null>(null)
  const [toDelete, setToDelete] = useState<AdminGeographyRow | null>(null)

  const kind: GeographyKind = region ? 'cities' : country ? 'regions' : 'countries'
  const parentId = region?.id ?? country?.id ?? null
  const nameOf = (row: AdminGeographyRow) => geographyName(row, language)

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchInput])

  // Doubles as the Try Again button and the refresh after every change
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const params = region ? { search, region: region.id } : country ? { search, country: country.id } : { search }
    const result = await adminGeographyAdapter.list(kind, params)
    if (result.data) setRows(result.data.results)
    else setLoadFailed(true)
    setLoading(false)
  }, [kind, search, country, region])

  useEffect(() => {
    void load()
  }, [load])

  const open = (row: AdminGeographyRow) => {
    setSearchInput('')
    setSearch('')
    setRows(null)
    if (kind === 'countries') setCountry(row as AdminCountry)
    else setRegion(row as AdminRegion)
  }

  const goTo = (level: 'root' | 'country') => {
    setSearchInput('')
    setSearch('')
    setRows(null)
    setRegion(null)
    if (level === 'root') setCountry(null)
  }

  const runAction = async (action: () => Promise<{ error: string | null }>) => {
    setBusy(true)
    setActionError(null)
    const { error } = await action()
    setBusy(false)
    if (error) setActionError(error)
    else await load()
  }

  const toggleActive = (row: AdminGeographyRow) =>
    runAction(() => adminGeographyAdapter.update(kind, row.id, { is_active: !row.is_active }))

  const move = (index: number, step: -1 | 1) => {
    const ids = (rows ?? []).map(row => row.id)
    ;[ids[index], ids[index + step]] = [ids[index + step], ids[index]]
    return runAction(() => adminGeographyAdapter.reorder(kind, ids))
  }

  const confirmDelete = async () => {
    if (!toDelete) return
    setBusy(true)
    const { error, inUse } = await adminGeographyAdapter.remove(kind, toDelete.id)
    setBusy(false)
    setToDelete(null)
    if (error) {
      setActionError(inUse ? t('geoAdmin.inUse') : error)
      return
    }
    setActionError(null)
    await load()
  }

  const reorderLocked = search !== ''
  const list = rows ?? []

  return (
    <div className="admin-geography">
      <h2 className="admin-view-title">{t('geoAdmin.title')}</h2>
      <p className="admin-view-subtitle">{t('geoAdmin.subtitle')}</p>

      <nav className="geography-trail" aria-label={t('geoAdmin.title')}>
        {country || region ? (
          <button type="button" className="btn btn-link" onClick={() => goTo('root')}>{t('geoAdmin.root')}</button>
        ) : (
          <span>{t('geoAdmin.root')}</span>
        )}
        {country && (region
          ? <button type="button" className="btn btn-link" onClick={() => goTo('country')}>{nameOf(country)}</button>
          : <span>{nameOf(country)}</span>)}
        {region && <span>{nameOf(region)}</span>}
      </nav>

      <h3 className="admin-section-title">{t(`geoAdmin.kind.${kind}`)}</h3>
      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="geography-search" className="search-label">{t('geoAdmin.search')}</label>
          <input id="geography-search" type="search" className="search-input" value={searchInput}
            onChange={e => setSearchInput(e.target.value)} />
        </div>
        <button type="button" className="btn btn-primary" onClick={() => setDialog({})}>{t(`geoAdmin.new.${kind}`)}</button>
      </div>
      {reorderLocked && <p className="geography-picker-hint">{t('geoAdmin.orderNeedsFullList')}</p>}

      {actionError && <p className="alert alert-error" role="alert">{actionError}</p>}
      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('geoAdmin.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && rows === null && !loadFailed && <p className="loading-state">{t('geoAdmin.loading')}</p>}
      {!loading && !loadFailed && list.length === 0 && <p className="empty-state">{t('geoAdmin.empty')}</p>}

      {list.length > 0 && (
        <div className="customers-table-container table-scroll">
          <table className="customers-table geography-table">
            <thead>
              <tr>
                {kind !== 'cities' && <th>{t('geoAdmin.col.picture')}</th>}
                <th>{t('geoAdmin.col.name')}</th>
                {kind === 'countries' && <th>{t('geoAdmin.col.code')}</th>}
                {kind !== 'cities' && <th>{t('geoAdmin.col.children')}</th>}
                <th>{t('geoAdmin.col.hotels')}</th>
                <th>{t('geoAdmin.col.status')}</th>
                <th>{t('geoAdmin.col.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {list.map((row, index) => {
                const name = nameOf(row)
                const children = 'region_count' in row ? row.region_count : 'city_count' in row ? row.city_count : null
                return (
                  <tr key={row.id}>
                    {kind !== 'cities' && (
                      <td data-label={t('geoAdmin.col.picture')}>
                        {'image_url' in row && row.image_url
                          ? <img className="geography-thumb" src={row.image_url} alt={t('geoAdmin.imageOf', { name })} loading="lazy" />
                          : <span className="geography-thumb geography-thumb--empty" aria-label={t('geoAdmin.noImage')} />}
                      </td>
                    )}
                    <td data-label={t('geoAdmin.col.name')}>{name}</td>
                    {kind === 'countries' && <td data-label={t('geoAdmin.col.code')}>{'code' in row ? row.code : ''}</td>}
                    {kind !== 'cities' && <td data-label={t('geoAdmin.col.children')}>{children}</td>}
                    <td data-label={t('geoAdmin.col.hotels')}>{row.hotel_count}</td>
                    <td data-label={t('geoAdmin.col.status')}>
                      <span className={`status-badge status-badge--${row.is_active ? 'active' : 'cancelled'}`}>
                        {row.is_active ? t('geoAdmin.active') : t('geoAdmin.hidden')}
                      </span>
                    </td>
                    <td data-label={t('geoAdmin.col.actions')}>
                      <div className="table-actions">
                        {kind !== 'cities' && (
                          <button type="button" className="btn btn-secondary btn-sm" aria-label={t('geoAdmin.openRow', { name })}
                            onClick={() => open(row)}>{t('geoAdmin.openBtn')}</button>
                        )}
                        <button type="button" className="btn btn-secondary btn-sm" aria-label={t('geoAdmin.editRow', { name })}
                          onClick={() => setDialog({ row })}>{t('geoAdmin.editBtn')}</button>
                        <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                          aria-label={t(row.is_active ? 'geoAdmin.hideRow' : 'geoAdmin.showRow', { name })}
                          onClick={() => void toggleActive(row)}>{t(row.is_active ? 'geoAdmin.hideBtn' : 'geoAdmin.showBtn')}</button>
                        <button type="button" className="btn btn-secondary btn-sm" aria-label={t('geoAdmin.upRow', { name })}
                          disabled={busy || reorderLocked || index === 0} onClick={() => void move(index, -1)}><ArrowUp size={16} aria-hidden="true" /></button>
                        <button type="button" className="btn btn-secondary btn-sm" aria-label={t('geoAdmin.downRow', { name })}
                          disabled={busy || reorderLocked || index === list.length - 1} onClick={() => void move(index, 1)}><ArrowDown size={16} aria-hidden="true" /></button>
                        <button type="button" className="btn btn-danger btn-sm" aria-label={t('geoAdmin.deleteRow', { name })}
                          onClick={() => setToDelete(row)}>{t('geoAdmin.deleteTitle')}</button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {dialog && (
        <GeographyRowDialog kind={kind} parentId={parentId} row={dialog.row}
          onSaved={() => { setDialog(null); void load() }} onClose={() => setDialog(null)} />
      )}
      {toDelete && (
        <DialogModal titleId="geography-delete-title" title={t('geoAdmin.deleteTitle')} onClose={() => setToDelete(null)}>
          <p>{t('geoAdmin.deleteConfirm', { name: nameOf(toDelete) })}</p>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setToDelete(null)}>{t('geoAdmin.cancel')}</button>
            <button type="button" className="btn btn-danger" disabled={busy} onClick={() => void confirmDelete()}>{t('geoAdmin.deleteTitle')}</button>
          </div>
        </DialogModal>
      )}
    </div>
  )
}
