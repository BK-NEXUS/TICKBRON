import { useState } from 'react'
import { DateInventory } from '../adapters/searchAdapter'

interface AvailabilityCalendarProps {
  inventory: DateInventory[]
  currency?: string
  onDateSelect?: (date: string) => void
  selectedDate?: string
}

/**
 * AvailabilityCalendar component for displaying date-based availability
 * Shows a calendar view with availability status, pricing, and booking constraints
 */
export function AvailabilityCalendar({ 
  inventory, 
  currency = 'USD', 
  onDateSelect, 
  selectedDate 
}: AvailabilityCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const formatPrice = (price: number, currencyCode: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startDayOfWeek = firstDay.getDay()

    const days = []
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null)
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      const inventoryItem = inventory.find(item => item.date === dateStr)
      days.push({
        date: dateStr,
        day,
        inventory: inventoryItem,
      })
    }

    return days
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentMonth(prev => {
      const newDate = new Date(prev)
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }

  const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  const days = getDaysInMonth(currentMonth)

  const getAvailabilityStatus = (inventoryItem?: DateInventory) => {
    if (!inventoryItem) return 'unavailable'
    if (!inventoryItem.is_available) return 'unavailable'
    if (inventoryItem.available_rooms <= inventoryItem.booked_rooms) return 'fully-booked'
    if (inventoryItem.available_rooms - inventoryItem.booked_rooms <= 1) return 'limited'
    return 'available'
  }

  const getAvailabilityColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'var(--color-success)'
      case 'limited':
        return 'var(--color-warning)'
      case 'fully-booked':
      case 'unavailable':
        return 'var(--color-error)'
      default:
        return 'var(--color-border)'
    }
  }

  if (inventory.length === 0) {
    return (
      <div className="availability-calendar availability-calendar--empty">
        <p className="availability-calendar-empty">No availability data available</p>
      </div>
    )
  }

  return (
    <div className="availability-calendar">
      <div className="availability-calendar-header">
        <button 
          className="availability-calendar-nav availability-calendar-nav--prev"
          onClick={() => navigateMonth('prev')}
          aria-label="Previous month"
        >
          ‹
        </button>
        <h3 className="availability-calendar-title">{monthName}</h3>
        <button 
          className="availability-calendar-nav availability-calendar-nav--next"
          onClick={() => navigateMonth('next')}
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      <div className="availability-calendar-weekdays">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="availability-calendar-weekday">
            {day}
          </div>
        ))}
      </div>

      <div className="availability-calendar-days">
        {days.map((dayData, index) => {
          if (!dayData) {
            return <div key={`empty-${index}`} className="availability-calendar-day availability-calendar-day--empty" />
          }

          const { date, day, inventory: inventoryItem } = dayData
          const status = getAvailabilityStatus(inventoryItem)
          const isSelected = selectedDate === date

          return (
            <div
              key={date}
              className={`availability-calendar-day availability-calendar-day--${status} ${
                isSelected ? 'availability-calendar-day--selected' : ''
              }`}
              onClick={() => inventoryItem?.is_available && onDateSelect?.(date)}
              role="button"
              tabIndex={inventoryItem?.is_available ? 0 : -1}
              aria-pressed={isSelected}
              aria-disabled={!inventoryItem?.is_available}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && inventoryItem?.is_available) {
                  e.preventDefault()
                  onDateSelect?.(date)
                }
              }}
            >
              <div className="availability-calendar-day-number">{day}</div>
              {inventoryItem && (
                <>
                  <div className="availability-calendar-day-price">
                    {formatPrice(inventoryItem.price, inventoryItem.currency)}
                  </div>
                  <div 
                    className="availability-calendar-day-indicator"
                    style={{ backgroundColor: getAvailabilityColor(status) }}
                    aria-label={`Availability: ${status}`}
                  />
                </>
              )}
            </div>
          )
        })}
      </div>

      <div className="availability-calendar-legend">
        <div className="availability-calendar-legend-item">
          <div 
            className="availability-calendar-legend-color"
            style={{ backgroundColor: 'var(--color-success)' }}
          />
          <span>Available</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div 
            className="availability-calendar-legend-color"
            style={{ backgroundColor: 'var(--color-warning)' }}
          />
          <span>Limited</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div 
            className="availability-calendar-legend-color"
            style={{ backgroundColor: 'var(--color-error)' }}
          />
          <span>Fully Booked</span>
        </div>
      </div>
    </div>
  )
}