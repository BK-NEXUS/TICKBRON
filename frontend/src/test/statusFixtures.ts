// Mocks shaped like the real R12a Status responses (.ai/API_CONTRACT.md "R12 phase 2").

import type {
  PartnerHotelStatus, PartnerStatus, StatusFullTotals, StatusHotelDetail, StatusReconciliation, StatusSeriesRow,
} from '../adapters/statusAdapter'

export const TOTALS: StatusFullTotals = {
  bookings: 1500,
  counted: 1500,
  stayed: 1380,
  guests: 3210,
  unique_customers: 1100,
  nights: 5400,
  room_nights: 6100,
  no_show: 0,
  no_show_reported: 0,
  fully_refunded: 0,
  upcoming: 42,
  revenue: [{ currency: 'UZS', amount: '1500000000.00' }, { currency: 'USD', amount: '45000.00' }],
  booking_value: [{ currency: 'UZS', amount: '1600000000.00' }],
  booking_status: { pending: 4, confirmed: 120, completed: 1380, cancelled: 30, expired: 5, no_show: 0, no_show_reported: 0 },
}

const window = (counted: [number, number], stayed: [number, number], from: string | null, to: string | null) => ({
  from, to, counted: { bookings: counted[0], guests: counted[1] }, stayed: { bookings: stayed[0], guests: stayed[1] },
})

export const RECONCILIATION: StatusReconciliation = {
  today: window([3, 7], [1, 2], '2026-10-07', '2026-10-07'),
  this_week: window([20, 41], [12, 25], '2026-10-05', '2026-10-11'),
  this_month: window([80, 170], [55, 120], '2026-10-01', '2026-10-31'),
  this_year: window([900, 1900], [800, 1700], '2026-01-01', '2026-12-31'),
  all_time: window([1500, 3210], [1380, 3000], null, null),
}

export const SERIES: StatusSeriesRow[] = [
  { period: '2026-08', start: '2026-08-01', bookings: 10, guests: 22, nights: 40, stayed: 9,
    revenue: [{ currency: 'USD', amount: '900.00' }, { currency: 'UZS', amount: '5000000.00' }] },
  { period: '2026-09', start: '2026-09-01', bookings: 0, guests: 0, nights: 0, stayed: 0, revenue: [] },
  { period: '2026-10', start: '2026-10-01', bookings: 5, guests: 11, nights: 20, stayed: 4,
    revenue: [{ currency: 'USD', amount: '300.00' }] },
]

export const HOTEL_DETAIL: StatusHotelDetail = {
  hotel: {
    id: 11, name: 'Alpha Hotel', status: 'active', address: '1 Alpha Street, Tashkent, Uzbekistan',
    city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan', registered_at: '2025-01-15T09:00:00Z',
    owner: { id: 5, name: 'Olim Owner', email: 'owner1@example.com', phone: '+998901111111' },
  },
  period: 'all',
  period_range: { from: null, to: null },
  totals: TOTALS,
  granularity: 'month',
  series: SERIES,
  reconciliation: RECONCILIATION,
  year: 2026,
  available_years: [2025, 2026],
  monthly: Array.from({ length: 12 }, (_, i) => ({
    month: `2026-${String(i + 1).padStart(2, '0')}`,
    bookings: i === 3 ? 2 : 0,
    guests: i === 3 ? 2 : 0,
    revenue: i === 3 ? [{ currency: 'USD', amount: '350.00' }] : [],
  })),
}

export const PARTNER_STATUS: PartnerStatus = {
  since: '2025-01-15',
  period: 'all',
  period_range: { from: null, to: null },
  totals: { ...TOTALS, bookings: 1205, counted: 1205, guests: 1003, revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '12530.00' }] },
  properties: [
    { id: 1, name: 'Alpha Hotel', city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan', status: 'active',
      bookings: 1203, guests: 1001, revenue: [{ currency: 'USD', amount: '12450.00' }] },
    { id: 2, name: 'Beta Hotel', city: 'Tashkent', region: 'Unspecified', country: 'Uzbekistan', status: 'active',
      bookings: 2, guests: 2, revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '80.00' }] },
  ],
  granularity: 'month',
  series: SERIES,
  reconciliation: RECONCILIATION,
  year: 2026,
  available_years: [2025, 2026],
  monthly: HOTEL_DETAIL.monthly,
}

export const PARTNER_HOTEL: PartnerHotelStatus = {
  hotel: { id: 1, name: 'Alpha Hotel', status: 'active', address: '1 Alpha Street', city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan' },
  period: 'all',
  period_range: { from: null, to: null },
  totals: TOTALS,
  granularity: 'month',
  series: SERIES,
  reconciliation: RECONCILIATION,
  year: 2026,
  available_years: [2026],
  monthly: HOTEL_DETAIL.monthly,
}
