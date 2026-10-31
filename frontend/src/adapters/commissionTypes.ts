// Commission figures (contract: .ai/API_CONTRACT.md, section "Commission"). Money is always a list per currency.

export interface MoneyLine {
  currency: string
  amount: string
}

/** Who confirmed that the owner paid a month, and the amounts at that moment */
export interface CommissionPaid {
  by: string
  role: 'super_admin' | 'staff'
  at: string
  amounts: MoneyLine[]
}

export interface CommissionMonth {
  /** "2026-05" */
  month: string
  bookings: number
  gross: MoneyLine[]
  /** null: no percent was set for that month, so there is no commission */
  percent: string | null
  commission: MoneyLine[] | null
  paid: CommissionPaid | null
}

export interface CommissionYear {
  year: number
  bookings: number
  gross: MoneyLine[]
  commission: MoneyLine[] | null
}

export interface CommissionStatement {
  percent: string | null
  percent_since: string | null
  months: CommissionMonth[]
  /** Only for an owner account that is at least a year old */
  years: CommissionYear[] | null
}

export interface CommissionOwnerRow {
  id: number
  name: string
  email: string
  phone_number: string | null
  percent: string | null
  this_month: { month: string; bookings: number; gross: MoneyLine[]; commission: MoneyLine[] | null }
  /** Commission of ended months that nobody confirmed as paid */
  unpaid: MoneyLine[]
}

export interface CommissionOwnerPage {
  count: number
  hasMore: boolean
  results: CommissionOwnerRow[]
}
