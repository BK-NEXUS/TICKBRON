import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { Link } from 'react-router-dom'

/**
 * Static information pages linked from the header and footer.
 * The legal texts are short plain-language summaries; they need a review
 * before a public launch.
 */
export type InfoPageSlug = 'about' | 'help' | 'contact' | 'safety' | 'terms' | 'privacy' | 'cookies'

interface Section {
  heading: MessageKey
  body: MessageKey
}

const PAGES: Record<InfoPageSlug, { title: MessageKey; intro: MessageKey; sections: Section[] }> = {
  about: {
    title: 'info.about.title',
    intro: 'info.about.intro',
    sections: [
      { heading: 'info.about.h1', body: 'info.about.b1' },
      { heading: 'info.about.h2', body: 'info.about.b2' },
    ],
  },
  help: {
    title: 'info.help.title',
    intro: 'info.help.intro',
    sections: [
      { heading: 'info.help.h1', body: 'info.help.b1' },
      { heading: 'info.help.h2', body: 'info.help.b2' },
      { heading: 'info.help.h3', body: 'info.help.b3' },
      { heading: 'info.help.h4', body: 'info.help.b4' },
    ],
  },
  contact: {
    title: 'info.contact.title',
    intro: 'info.contact.intro',
    sections: [
      { heading: 'info.contact.h1', body: 'info.contact.b1' },
      { heading: 'info.contact.h2', body: 'info.contact.b2' },
    ],
  },
  safety: {
    title: 'info.safety.title',
    intro: 'info.safety.intro',
    sections: [
      { heading: 'info.safety.h1', body: 'info.safety.b1' },
      { heading: 'info.safety.h2', body: 'info.safety.b2' },
      { heading: 'info.safety.h3', body: 'info.safety.b3' },
    ],
  },
  terms: {
    title: 'info.terms.title',
    intro: 'info.terms.intro',
    sections: [
      { heading: 'info.terms.h1', body: 'info.terms.b1' },
      { heading: 'info.terms.h2', body: 'info.terms.b2' },
      { heading: 'info.terms.h3', body: 'info.terms.b3' },
    ],
  },
  privacy: {
    title: 'info.privacy.title',
    intro: 'info.privacy.intro',
    sections: [
      { heading: 'info.privacy.h1', body: 'info.privacy.b1' },
      { heading: 'info.privacy.h2', body: 'info.privacy.b2' },
      { heading: 'info.privacy.h3', body: 'info.privacy.b3' },
    ],
  },
  cookies: {
    title: 'info.cookies.title',
    intro: 'info.cookies.intro',
    sections: [
      { heading: 'info.cookies.h1', body: 'info.cookies.b1' },
      { heading: 'info.cookies.h2', body: 'info.cookies.b2' },
      { heading: 'info.cookies.h3', body: 'info.cookies.b3' },
    ],
  },
}

export function InfoPage({ slug }: { slug: InfoPageSlug }) {
  const { t } = useI18n()
  const page = PAGES[slug]
  return (
    <div className="info-page container">
      <h1 className="info-page-title">{t(page.title)}</h1>
      <p className="info-page-intro">{t(page.intro)}</p>
      {page.sections.map(section => (
        <section key={section.heading} className="info-page-section">
          <h2>{t(section.heading)}</h2>
          <p>{t(section.body)}</p>
        </section>
      ))}
      <p className="info-page-footer">
        <Link to="/search" className="btn btn-primary">{t('info.browse')}</Link>
      </p>
    </div>
  )
}

export default InfoPage
