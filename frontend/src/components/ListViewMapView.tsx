interface ListViewMapViewProps {
  view: 'list' | 'map'
  onViewChange: (view: 'list' | 'map') => void
}

/**
 * ListViewMapView component for switching between list and map views
 * Provides toggle buttons for list and map presentation modes
 */
export function ListViewMapView({ view, onViewChange }: ListViewMapViewProps) {
  return (
    <div className="list-view-map-view" role="group" aria-label="View mode">
      <button
        className={`list-view-map-view-button ${view === 'list' ? 'list-view-map-view-button-active' : ''}`}
        onClick={() => onViewChange('list')}
        aria-label="List view"
        aria-pressed={view === 'list'}
      >
        <span className="list-view-map-view-icon">📋</span>
        <span className="list-view-map-view-label">List</span>
      </button>
      <button
        className={`list-view-map-view-button ${view === 'map' ? 'list-view-map-view-button-active' : ''}`}
        onClick={() => onViewChange('map')}
        aria-label="Map view"
        aria-pressed={view === 'map'}
      >
        <span className="list-view-map-view-icon">🗺️</span>
        <span className="list-view-map-view-label">Map</span>
      </button>
    </div>
  )
}