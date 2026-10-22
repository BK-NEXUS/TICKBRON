import { useCallback, useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import {
  geographyAdapter,
  geographyName,
  type GeographyCity,
  type GeographyCountry,
  type GeographyRegion,
} from '../adapters/geographyAdapter'

export interface GeographyValue {
  country_ref: number | null
  region_ref: number | null
  city_ref: number | null
}

/** Names of the chosen rows in the page language ('' = nothing chosen), for summaries. */
export interface GeographyLabels {
  country: string
  region: string
  city: string
}

interface GeographyPickerProps {
  value: GeographyValue
  onChange: (value: GeographyValue, labels: GeographyLabels) => void
  /** Called with the names of the chosen rows once they are loaded (for a value set from outside) */
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

/** Loads one list; `load` null means "nothing to load yet" (the parent is not chosen). */
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
    // `load` is rebuilt on every render; the key says when the request really differs
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

/** Country > Region > City dropdowns from the public geography dictionary, names in the page language. */
export function GeographyPicker({ value, onChange, onLabels, disabled = false, required = false }: GeographyPickerProps) {
  const { t, language } = useI18n()
  const id = useId()

  const countries = useList<GeographyCountry>(geographyAdapter.getCountries.bind(geographyAdapter), 'countries')
  const countryCode = countries.items.find(c => c.id === value.country_ref)?.code ?? null
  const regions = useList<GeographyRegion>(
    countryCode ? () => geographyAdapter.getRegions(countryCode) : null,
    `regions:${countryCode}`,
  )
  const cities = useList<GeographyCity>(
    value.region_ref !== null ? () => geographyAdapter.getCities(value.region_ref as number) : null,
    `cities:${value.region_ref}`,
  )

  const nameOf = (items: Array<{ id: number } & Record<'name_uz' | 'name_ru' | 'name_en', string>>, id: number | null) => {
    const row = items.find(item => item.id === id)
    return row ? geographyName(row, language) : ''
  }
  const labels = {
    country: nameOf(countries.items, value.country_ref),
    region: nameOf(regions.items, value.region_ref),
    city: nameOf(cities.items, value.city_ref),
  }
  useEffect(() => {
    onLabels?.(labels)
    // only when a name really changes; `onLabels` is rebuilt on every render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels.country, labels.region, labels.city])

  const emit = (next: GeographyValue) => onChange(next, {
    country: nameOf(countries.items, next.country_ref),
    region: nameOf(regions.items, next.region_ref),
    city: nameOf(cities.items, next.city_ref),
  })

  const parse = (raw: string) => (raw === '' ? null : Number(raw))
  const failed = countries.failed || regions.failed || cities.failed
  const retry = useCallback(() => {
    if (countries.failed) countries.reload()
    if (regions.failed) regions.reload()
    if (cities.failed) cities.reload()
  }, [countries, regions, cities])

  const select = (
    field: 'country' | 'region' | 'city',
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

  const noCities = value.region_ref !== null && !cities.loading && !cities.failed && cities.items.length === 0

  return (
    <div className="geography-picker">
      {select('country', t('geo.country'), value.country_ref, countries.items, countries.loading,
        next => emit({ country_ref: next, region_ref: null, city_ref: null }))}
      {select('region', t('geo.region'), value.region_ref, regions.items, value.country_ref === null || regions.loading,
        next => emit({ country_ref: value.country_ref, region_ref: next, city_ref: null }))}
      {select('city', t('geo.city'), value.city_ref, cities.items, value.region_ref === null || cities.loading,
        next => emit({ ...value, city_ref: next }))}
      {noCities && <p className="geography-picker-hint">{t('geo.noCities')}</p>}
      {failed && (
        <p role="alert" className="geography-picker-error">
          {t('geo.loadFailed')}{' '}
          <button type="button" className="btn btn-secondary btn-small" onClick={retry}>{t('geo.retry')}</button>
        </p>
      )}
    </div>
  )
}
