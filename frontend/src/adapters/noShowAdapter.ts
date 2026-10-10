// "Guest did not arrive" (R12b): the owner's reports and the staff queue.
// Contract: .ai/API_CONTRACT.md, section "R12b: no-show reports and the 50% refund".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/** What a guest is told about the no-show refund; the backend sends numbers and a text key, never the sentence. */
export interface NoShowRefundInfo {
  no_show_refund_percent?: number
  no_show_refund_amount?: string | null
  no_show_refund_text_key?: string | null
  no_show_refund_text_params?: { percent: number; amount: string | null } | null
}

export type NoShowReportStatus = 'pending' | 'approved' | 'rejected' | 'withdrawn'

export interface OwnerNoShowReport {
  id: number
  booking_id: number
  booking_reference: string
  property_id: number
  property_name: string
  check_in: string
  check_out: string
  comment: string
  status: NoShowReportStatus
  decision_comment: string
  decided_at: string | null
  created_at: string
}

/** Exact amounts the backend would refund if the report is approved now (strings, never computed here). */
export interface RefundPreview {
  amount: string
  currency: string
  percent: number
  already_refunded: string
  paid: string
}

export interface StaffNoShowReport extends OwnerNoShowReport {
  decided_by_id: number | null
  created_by_id: number | null
  hotel_flagged: boolean
  refund_preview: RefundPreview | null
  refunds: Array<{ id: number; amount: string; currency: string; status: string }>
}

export interface ReportPage<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface OwnerReportParams {
  status?: string
  property?: number
  page?: number
}

export interface StaffReportParams extends OwnerReportParams {
  from?: string
  to?: string
}

/** `code` is the backend's stable error name; `fieldErrors` carries comment validation messages. */
export interface NoShowResult<T> {
  data: T | null
  error: string | null
  code: string | null
  fieldErrors: Record<string, string[]> | null
}

const OWNER = '/api/v1/partner'
const STAFF = '/api/v1/admin-panel/no-show-reports'
const STATUS_MESSAGES = { 401: 'Authentication required', 403: 'Access denied', 404: 'Report not found' }

function withQuery(path: string, params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.append(key, String(value))
  }
  const text = query.toString()
  return text ? `${path}?${text}` : path
}

export class NoShowAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<NoShowResult<T>> {
    try {
      const response = await apiFetch(`${this.baseUrl}${endpoint}`, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (!response.ok) {
        const apiError = await readApiError(response, STATUS_MESSAGES)
        return { data: null, error: apiError.message, code: apiError.code ?? null, fieldErrors: apiError.fieldErrors ?? null }
      }
      return { data: (await response.json()) as T, error: null, code: null, fieldErrors: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : 'Network error occurred', code: null, fieldErrors: null }
    }
  }

  private post<T>(endpoint: string, body?: unknown): Promise<NoShowResult<T>> {
    return this.request<T>(endpoint, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
  }

  // Owner

  reportNoShow(bookingId: number, comment: string): Promise<NoShowResult<OwnerNoShowReport>> {
    return this.post(`${OWNER}/bookings/${bookingId}/no-show-report/`, { comment })
  }

  listMyReports(params: OwnerReportParams = {}): Promise<NoShowResult<ReportPage<OwnerNoShowReport>>> {
    return this.request(withQuery(`${OWNER}/no-show-reports/`, { ...params }))
  }

  withdrawReport(reportId: number): Promise<NoShowResult<OwnerNoShowReport>> {
    return this.post(`${OWNER}/no-show-reports/${reportId}/withdraw/`)
  }

  // Staff and super-admin

  listReports(params: StaffReportParams = {}): Promise<NoShowResult<ReportPage<StaffNoShowReport>>> {
    return this.request(withQuery(`${STAFF}/`, { ...params }))
  }

  approveReport(reportId: number, decisionComment: string): Promise<NoShowResult<StaffNoShowReport>> {
    return this.post(`${STAFF}/${reportId}/approve/`, { decision_comment: decisionComment })
  }

  rejectReport(reportId: number, decisionComment: string): Promise<NoShowResult<StaffNoShowReport>> {
    return this.post(`${STAFF}/${reportId}/reject/`, { decision_comment: decisionComment })
  }

  reverseReport(reportId: number, decisionComment: string): Promise<NoShowResult<StaffNoShowReport>> {
    return this.post(`${STAFF}/${reportId}/reverse/`, { decision_comment: decisionComment })
  }
}

export const noShowAdapter = new NoShowAdapter()
