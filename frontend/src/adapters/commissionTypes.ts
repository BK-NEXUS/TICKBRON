// Komissiya sanları (contract: .ai/API_CONTRACT.md, "Commission" bólimi). Pul hárdayım hár valyuta boyınsha dizim.

export interface MoneyLine {
  currency: string
  amount: string
}

/** Iye bir ayın tólegenin kim tastıyıqladı, hám sol waqıttaǵı summalar */
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
  /** null: sol ay ushın procent belgilenbegen, sol sebepli komissiya joq */
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
  /** Tek eń keminde bir jıllıq iye akkaunt ı ushın */
  years: CommissionYear[] | null
}

export interface CommissionOwnerRow {
  id: number
  name: string
  email: string
  phone_number: string | null
  percent: string | null
  this_month: { month: string; bookings: number; gross: MoneyLine[]; commission: MoneyLine[] | null }
  /** Hesh kim tólengen dep tastıyıqlamaǵan pitken aylardıń komissiyası */
  unpaid: MoneyLine[]
}

export interface CommissionOwnerPage {
  count: number
  hasMore: boolean
  results: CommissionOwnerRow[]
}
