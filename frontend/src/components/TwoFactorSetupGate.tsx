import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export const TWO_FACTOR_SETUP_PATH = '/two-factor-setup'

/** An administrator who has not set up two-step sign-in can only see the setup page (the backend refuses everything else). */
export function TwoFactorSetupGate({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const { pathname } = useLocation()

  if (user?.two_factor_setup_required && pathname !== TWO_FACTOR_SETUP_PATH) {
    return <Navigate to={TWO_FACTOR_SETUP_PATH} replace />
  }
  return <>{children}</>
}
