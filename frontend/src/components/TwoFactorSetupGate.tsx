import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useAuth } from '../contexts/AuthContext'

export const TWO_FACTOR_SETUP_PATH = '/two-factor-setup'

/** Eki basqıshlı kirisiwdi sazlamaǵan administrator tek sazlaw betin kóre aladı (backend basqa hámmesin qabıllamaydı). */
export function TwoFactorSetupGate({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const { pathname } = useLocation()

  if (user?.two_factor_setup_required && pathname !== TWO_FACTOR_SETUP_PATH) {
    return <Navigate to={TWO_FACTOR_SETUP_PATH} replace />
  }
  return <>{children}</>
}
