import { Outlet } from 'react-router-dom'
import { Header } from '../components/Header'
import { Footer } from '../components/Footer'
import { MobileBottomNavigation } from '../components/MobileBottomNavigation'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'

export function MainLayout() {
  return (
    <BreadcrumbProvider>
      <div className="main-layout">
        <Header />
        <main className="main-content">
          <Breadcrumbs />
          <Outlet />
        </main>
        <Footer />
        <MobileBottomNavigation />
      </div>
    </BreadcrumbProvider>
  )
}
