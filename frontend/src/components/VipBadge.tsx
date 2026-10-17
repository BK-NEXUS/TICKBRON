import { Crown } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

/** The mark of a VIP room type (the hotel owner sets it; guests see it on the room and in the booking summary). */
export function VipBadge() {
  const { t } = useI18n()
  return (
    <span className="vip-badge" aria-label={t('vip.badgeLabel')}>
      <Crown size={12} aria-hidden="true" /> {t('vip.badge')}
    </span>
  )
}
