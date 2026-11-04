import { LanguageSwitch } from './components/LanguageSwitch'
import { ThemeToggle } from './components/ThemeToggle'
import { profile } from './data/profile'
import { useI18n } from './i18n/context'
import { I18nProvider } from './i18n/I18nProvider'
import { SceneLayer } from './scene/SceneLayer'
import { About } from './sections/About'
import { Certificates } from './sections/Certificates'
import { Contact } from './sections/Contact'
import { Hero } from './sections/Hero'
import { Website } from './sections/Website'
import { ThemeProvider } from './theme/ThemeProvider'

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
        <div className="topbar-tools">
          <LanguageSwitch />
          <ThemeToggle />
        </div>
      </header>
      <main>
        <Hero />
        <About />
        <Certificates certificates={profile.certificates} />
        <Website />
        <Contact />
      </main>
      <a className="contact-bar" href="#contact">
        {t('contact.title')}
      </a>
    </>
  )
}

export default function App() {
  return (
    <I18nProvider>
      <ThemeProvider>
        <Page />
      </ThemeProvider>
    </I18nProvider>
  )
}
