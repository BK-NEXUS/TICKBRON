import { useCallback, useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import {
  geographyAdapter,
  geographyName,
  type GeographyCountry,
  type GeographyRegion,
} from '../adapters/geographyAdapter'

export interface GeographyValue {
  country_ref: number | null
  region_ref: number | null
}

/** Tańlanǵan qatarlardıń bet tilindegi atları ('' = hesh nárse tańlanbaǵan), qısqasha mazmun ushın. */
export interface GeographyLabels {
  country: string
  region: string
}

interface GeographyPickerProps {
  value: GeographyValue
  onChange: (value: GeographyValue, labels: GeographyLabels) => void
  /** Tańlanǵan qatarlardıń atları júklengennen keyin shaqırıladı (sırttan belgilengen mánis ushın) */
  onLabels?: (labels: GeographyLabels) => void
  disabled?: boolean
  required?: boolean
}

interface LoadedList<T> {
  items: T[]
  loading: boolean
  failed: boolean
  reload: () => void
}

let countriesRequest: ReturnType<typeof geographyAdapter.getCountries> | null = null

/**
 * Birdey waqıtta ornatılatuǵın tańlaǵıshlar (hár moderation kartasına bir) mámleketler ushın bir soraw bóliskenledi.
 * Tek sol waqıtta: keyin ornatılǵan tańlaǵısh qayta soraydı, sol sebepli sekin yamasa qatıp qalǵan soraw onı hesh qashan tosıp
 * qoymaydı.
 */
function loadCountries() {
  if (countriesRequest === null) {
    countriesRequest = geographyAdapter.getCountries()
    setTimeout(() => { countriesRequest = null }, 0)
  }
  return countriesRequest
}

/** Bir dizimdi júkleydi; `load` null "ele júklew kerek emes" degendi bildiredi (ata-ana tańlanbaǵan). */
function useList<T>(load: (() => Promise<{ data: T[] | null; error: string | null }>) | null, key: string): LoadedList<T> {
  const [state, setState] = useState<{ key: string; items: T[]; failed: boolean } | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (!load) return
    let current = true
    load().then(({ data, error }) => {
      if (current) setState({ key, items: data ?? [], failed: error !== null })
    })
    return () => { current = false }
    // `load` hár render de qayta quriladı; kilt soraw haqıyqatında ayırmashılıqlı bolǵanda aytadı
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt])

  const ready = load !== null && state?.key === key
  return {
    items: ready ? state.items : [],
    loading: load !== null && !ready,
    failed: ready && state.failed,
    reload: () => { setState(null); setAttempt(n => n + 1) },
  }
}

/** Ashıq geografiya sózliginen Country > Region dropdown ları, atlar bet tilinde. */
export function GeographyPicker({ value, onChange, onLabels, disabled = false, required = false }: GeographyPickerProps) {
  const { t, language } = useI18n()
  const id = useId()

  const countries = useList<GeographyCountry>(loadCountries, 'countries')
  const countryCode = countries.items.find(c => c.id === value.country_ref)?.code ?? null
  const regions = useList<GeographyRegion>(
    countryCode ? () => geographyAdapter.getRegions(countryCode) : null,
    `regions:${countryCode}`,
  )

  const nameOf = (items: Array<{ id: number } & Record<'name_uz' | 'name_ru' | 'name_en', string>>, id: number | null) => {
    const row = items.find(item => item.id === id)
    return row ? geographyName(row, language) : ''
  }
  const labels = {
    country: nameOf(countries.items, value.country_ref),
    region: nameOf(regions.items, value.region_ref),
  }
  useEffect(() => {
    onLabels?.(labels)
    // tek at haqıyqatında ózgergende; `onLabels` hár render de qayta quriladı
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels.country, labels.region])

  const emit = (next: GeographyValue) => onChange(next, {
    country: nameOf(countries.items, next.country_ref),
    region: nameOf(regions.items, next.region_ref),
  })

  const parse = (raw: string) => (raw === '' ? null : Number(raw))
  const failed = countries.failed || regions.failed
  const retry = useCallback(() => {
    if (countries.failed) countries.reload()
    if (regions.failed) regions.reload()
  }, [countries, regions])

  const select = (
    field: 'country' | 'region',
    label: string,
    current: number | null,
    items: Array<{ id: number } & Record<'name_uz' | 'name_ru' | 'name_en', string>>,
    isDisabled: boolean,
    onPick: (next: number | null) => void,
  ) => (
    <div className="form-group">
      <label htmlFor={`${id}-${field}`}>{label}</label>
      <select
        id={`${id}-${field}`}
        className="form-input"
        value={current ?? ''}
        disabled={disabled || isDisabled}
        aria-required={required}
        onChange={event => onPick(parse(event.target.value))}
      >
        <option value="">{t('geo.choose')}</option>
        {items.map(item => (
          <option key={item.id} value={item.id}>{geographyName(item, language)}</option>
        ))}
      </select>
    </div>
  )

  return (
    <div className="geography-picker">
      {select('country', t('geo.country'), value.country_ref, countries.items, countries.loading,
        next => emit({ country_ref: next, region_ref: null }))}
      {select('region', t('geo.region'), value.region_ref, regions.items, value.country_ref === null || regions.loading,
        next => emit({ country_ref: value.country_ref, region_ref: next }))}
      {failed && (
        <p role="alert" className="geography-picker-error">
          {t('geo.loadFailed')}{' '}
          <button type="button" className="btn btn-secondary btn-small" onClick={retry}>{t('geo.retry')}</button>
        </p>
      )}
    </div>
  )
}
