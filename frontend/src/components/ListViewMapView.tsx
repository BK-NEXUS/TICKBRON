import { List, Map as MapIcon } from 'lucide-react'
import { SegmentedControl, type SegmentedOption } from './SegmentedControl'
import { useI18n } from '../i18n/I18nContext'

type View = 'list' | 'map'

interface ListViewMapViewProps {
  view: View
  onViewChange: (view: View) => void
}

/**
 * Dizim hám karta kórinisleri arasında almastırıw ushın ListViewMapView komponenti
 * Dizim hám karta kórsetiw rejimleri ushın almastırıw túymelerin usınadı
 */
export function ListViewMapView({ view, onViewChange }: ListViewMapViewProps) {
  const { t } = useI18n()
  const options: SegmentedOption<View>[] = [
    {
      value: 'list',
      ariaLabel: t('view.listLabel'),
      className: 'list-view-map-view-button',
      activeClassName: 'list-view-map-view-button-active',
      label: (
        <>
          <List className="list-view-map-view-icon" size={18} aria-hidden="true" />
          <span className="list-view-map-view-label">{t('view.list')}</span>
        </>
      ),
    },
    {
      value: 'map',
      ariaLabel: t('view.mapLabel'),
      className: 'list-view-map-view-button',
      activeClassName: 'list-view-map-view-button-active',
      label: (
        <>
          <MapIcon className="list-view-map-view-icon" size={18} aria-hidden="true" />
          <span className="list-view-map-view-label">{t('view.map')}</span>
        </>
      ),
    },
  ]
  return <SegmentedControl aria-label={t('view.mode')} options={options} value={view} onChange={onViewChange} />
}
