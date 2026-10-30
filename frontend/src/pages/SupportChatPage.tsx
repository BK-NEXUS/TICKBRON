import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { Lock } from 'lucide-react'
import { chatAdapter } from '../adapters/chatAdapter'
import { ChatThread } from '../components/ChatThread'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { canUsePartnerPanel } from '../utils/roles'

export default function SupportChatPage() {
  const { t } = useI18n()
  const { isAuthenticated, user } = useAuth()
  const [params] = useSearchParams()
  const api = useMemo(() => chatAdapter.mine(), [])
  const isOwner = Boolean(user && canUsePartnerPanel(user))
  const wantsAds = params.get('topic') === 'ads'

  if (!isAuthenticated) {
    return (
      <div className="support-chat-page">
        <div className="container">
          <EmptyState
            headingLevel={1}
            icon={<Lock size={40} />}
            title={t('common.signInRequired')}
            message={t('chat.signInText')}
            ctaText={t('auth.signIn')}
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="support-chat-page">
      <div className="container support-chat-page__inner">
        <h1>{t('chat.title')}</h1>
        <p className="support-chat-page__intro">{t('chat.intro')}</p>
        {isOwner && !wantsAds && (
          <p className="support-chat-page__hint">
            <Link to="/support?topic=ads">{t('chat.adsHint')}</Link>
          </p>
        )}
        <ChatThread api={api} side="guest" emptyText={t('chat.empty')} initialText={wantsAds ? t('chat.adsTemplate') : ''} />
      </div>
    </div>
  )
}
