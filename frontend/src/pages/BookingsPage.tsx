import { EmptyState } from '../components/EmptyState'

export function BookingsPage() {
  return (
    <div className="bookings-page">
      <div className="container">
        <EmptyState
          icon="📅"
          title="No bookings yet"
          message="Start exploring amazing properties and book your first stay."
          ctaText="Search Properties"
          ctaLink="/"
        />
      </div>
    </div>
  )
}
