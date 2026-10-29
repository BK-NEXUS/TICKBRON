import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { OwnerHotelRating } from './OwnerHotelRating'
import { I18nProvider } from '../i18n/I18nContext'
import type { ReviewSummary } from '../adapters/statusAdapter'

const SUMMARY: ReviewSummary = {
  count: 3, average: '4.3', distribution: [0, 0, 0, 2, 1],
  categories: { cleanliness: '4.5', location: '4.0', value: '3.0', amenities: null, service: null },
}

function show(summary: ReviewSummary) {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><OwnerHotelRating hotelId={7} reviews={summary} /></I18nProvider>)
}

describe('OwnerHotelRating', () => {
  it('shows the average, the number of reviews and the categories that guests rated', () => {
    show(SUMMARY)
    expect(screen.getByRole('heading', { name: 'Guest reviews' })).toBeInTheDocument()
    expect(screen.getByText('4.3')).toBeInTheDocument()
    expect(screen.getByText('3 reviews')).toBeInTheDocument()
    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.queryByText('Service')).not.toBeInTheDocument()
  })

  it('shows how many reviews gave each number of stars, five first', () => {
    show(SUMMARY)
    const rows = screen.getAllByRole('listitem')
    const cell = (row: HTMLElement, name: string) => row.querySelector(`.owner-rating-split-${name}`)?.textContent
    expect(rows.map(row => cell(row, 'label'))).toEqual(['5', '4', '3', '2', '1'])
    expect(rows.map(row => cell(row, 'count'))).toEqual(['1', '2', '0', '0', '0'])
    expect(within(rows[0]).getByRole('img', { name: '1 of 3 reviews gave 5 stars' })).toBeInTheDocument()
  })

  it('says that the numbers are all time, not the period of the page', () => {
    show(SUMMARY)
    expect(screen.getByText(/all time/i)).toBeInTheDocument()
  })

  it('has an empty state without the split', () => {
    show({ count: 0, average: null, distribution: [0, 0, 0, 0, 0], categories: {
      cleanliness: null, location: null, value: null, amenities: null, service: null } })
    expect(screen.getByText('No reviews yet')).toBeInTheDocument()
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
  })
})
