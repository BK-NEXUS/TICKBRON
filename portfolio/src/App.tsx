import { LanguageSwitch } from './components/LanguageSwitch'
import { profile } from './data/profile'
import { useI18n } from './i18n/context'
import { I18nProvider } from './i18n/I18nProvider'
import { About } from './sections/About'
import { Certificates } from './sections/Certificates'
import { Contact } from './sections/Contact'
import { Hero } from './sections/Hero'
import { SceneLayer } from './scene/SceneLayer'
import { Website } from './sections/Website'

const NAV = [
  { href: '#about', key: 'nav.about' },
  { href: '#certificates', key: 'nav.certificates' },
  { href: '#website', key: 'nav.website' },
  { href: '#contact', key: 'nav.contact' },
]

function Page() {
  const { t } = useI18n()
  return (
    <>
      <SceneLayer />
      <header className="topbar">
        <nav aria-label="Main">
          {NAV.map((item) => (
            <a key={item.href} href={item.href}>
              {t(item.key)}
            </a>
          ))}
        </nav>
        <LanguageSwitch />
      </header>
      <main>
        <Hero />
        <About />
        <Certificates certificates={profile.certificates} />
        <Website />
        <Contact />
      </main>
    </>
  )
}

export default function App() {
  return (
    <I18nProvider>
      <Page />
    </I18nProvider>
  )
}
