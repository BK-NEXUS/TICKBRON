import { List, Map as MapIcon } from 'lucide-react'
import { SegmentedControl, type SegmentedOption } from './SegmentedControl'

type View = 'list' | 'map'

interface ListViewMapViewProps {
  view: View
  onViewChange: (view: View) => void
}

const OPTIONS: SegmentedOption<View>[] = [
  {
    value: 'list',
    ariaLabel: 'List view',
    className: 'list-view-map-view-button',
    activeClassName: 'list-view-map-view-button-active',
    label: (
      <>
        <List className="list-view-map-view-icon" size={18} aria-hidden="true" />
        <span className="list-view-map-view-label">List</span>
      </>
    ),
  },
  {
    value: 'map',
    ariaLabel: 'Map view',
    className: 'list-view-map-view-button',
    activeClassName: 'list-view-map-view-button-active',
    label: (
      <>
        <MapIcon className="list-view-map-view-icon" size={18} aria-hidden="true" />
        <span className="list-view-map-view-label">Map</span>
      </>
    ),
  },
]

/**
 * ListViewMapView component for switching between list and map views
 * Provides toggle buttons for list and map presentation modes
 */
export function ListViewMapView({ view, onViewChange }: ListViewMapViewProps) {
  return <SegmentedControl aria-label="View mode" options={OPTIONS} value={view} onChange={onViewChange} />
}
