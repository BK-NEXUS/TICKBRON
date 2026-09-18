import { Outlet } from 'react-router-dom'
import { Header } from '../components/Header'
import { Footer } from '../components/Footer'
import { MobileBottomNavigation } from '../components/MobileBottomNavigation'

export function MainLayout() {
  return (
    <div className="main-layout">
      <Header />
      <main className="main-content">
        <Outlet />
      </main>
      <Footer />
      <MobileBottomNavigation />
    </div>
  )
}
