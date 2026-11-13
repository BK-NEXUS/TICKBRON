import { Crown } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

/** VIP xona túriniń belgisi (mehmanxana iyesi belgileydi; mehmanlar onı xonada hám bron qısqasha mazmunında kóredi). */
export function VipBadge() {
  const { t } = useI18n()
  return (
    <span className="vip-badge" aria-label={t('vip.badgeLabel')}>
      <Crown size={12} aria-hidden="true" /> {t('vip.badge')}
    </span>
  )
}
