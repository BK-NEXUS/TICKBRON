import { useI18n } from '../i18n/I18nContext'
import type { NoShowRefundInfo } from '../adapters/noShowAdapter'

// The only sentence the backend can ask for; any other key means the frontend is older than the backend
const STATEMENT_KEY = 'no_show_refund_statement'

interface NoShowRefundNoteProps {
  info: NoShowRefundInfo | null | undefined
}

/**
 * The no-show refund promise, shown before payment, on the confirmation and in "My bookings".
 * The percent and the amount are printed exactly as the backend sent them; nothing is calculated here.
 */
export function NoShowRefundNote({ info }: NoShowRefundNoteProps) {
  const { t, formatMoney } = useI18n()
  const params = info?.no_show_refund_text_params
  if (!info || !params || info.no_show_refund_text_key !== STATEMENT_KEY || !(Number(info.no_show_refund_percent) > 0)) {
    return null
  }
  const text = params.amount
    ? t('no_show_refund_statement', { percent: params.percent, amount: formatMoney(params.amount, 'UZS', { minDecimals: 0, maxDecimals: 0 }) })
    : t('no_show_refund_statement_percent', { percent: params.percent })
  return <p className="no-show-refund-note" data-testid="no-show-refund-note">{text}</p>
}
