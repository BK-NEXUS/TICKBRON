// Exchange rates of the Central Bank of Uzbekistan: history for staff, status and acceptance for the super-admin.
// Contract: .ai/API_CONTRACT.md, section "Currency: UZS charge, CBU rate, booking snapshot (R6)".
import { apiFetch, type Paginated } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import { translateNow } from '../i18n/translateNow'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const PAGE_SIZE = 20

export interface ExchangeRateRow {
  id: number
  currency: string
  /** UZS per `nominal` units, 6 decimals as a string */
  rate: string
  nominal: number
  rate_date: string
  source: string
  status: 'accepted' | 'rejected'
  note: string
  fetched_at: string
}

export interface CurrencyRateStatus {
  currency: string
  rate: string | null
  date: string | null
  source: string | null
  stale: boolean
  last_fetch: { attempted_at: string; success: boolean; error: string } | null
  last_error: string | null
  rejected: ExchangeRateRow[]
}

export interface ExchangeRateStatus {
  currencies: CurrencyRateStatus[]
}

type Result<T> = { data: T | null; error: string | null; status?: number }

export class ExchangeRateAdapter {
  constructor(private baseUrl: string = API_BASE_URL) {}

  private async send<T>(path: string, init: RequestInit = {}): Promise<Result<T>> {
    try {
      const response = await apiFetch(`${this.baseUrl}/api/v1/admin-panel/exchange-rates/${path}`, init)
      if (!response.ok) {
        return { data: null, error: (await readApiError(response)).message, status: response.status }
      }
      return { data: await response.json(), error: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred') }
    }
  }

  list({ page = 1 }: { page?: number } = {}) {
    return this.send<Paginated<ExchangeRateRow>>(`?page=${page}&page_size=${PAGE_SIZE}`)
  }

  status() {
    return this.send<ExchangeRateStatus>('status/')
  }

  /** The backend jumps over its change limit only when a super-admin accepts a rejected rate; it is audit-logged. */
  accept(id: number) {
    return this.send<ExchangeRateRow>(`${id}/accept/`, { method: 'POST' })
  }
}

export const exchangeRateAdapter = new ExchangeRateAdapter()
export const EXCHANGE_RATE_PAGE_SIZE = PAGE_SIZE
