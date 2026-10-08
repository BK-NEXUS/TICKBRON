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
        <span className="list-view-map-view-icon">📋</span>
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
        <span className="list-view-map-view-icon">🗺️</span>
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
