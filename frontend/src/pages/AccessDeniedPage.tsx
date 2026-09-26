import { Link } from 'react-router-dom'

interface AccessDeniedPageProps {
  /** What the visitor tried to open, e.g. "the admin dashboard" */
  area: string
  /** Anonymous visitors also get a sign-in link */
  signedIn: boolean
}

export function AccessDeniedPage({ area, signedIn }: AccessDeniedPageProps) {
  return (
    <div className="access-denied-page">
      <div className="container">
        <div className="access-denied-card" role="alert">
          <div className="access-denied-icon" aria-hidden="true">🔒</div>
          <h1 className="access-denied-title">Access Denied</h1>
          <p className="access-denied-message">
            {signedIn
              ? `Your account does not have permission to open ${area}.`
              : `Please sign in with an account that has access to ${area}.`}
          </p>
          <div className="access-denied-actions">
            <Link to="/" className="btn btn-primary">Back to Home</Link>
            {!signedIn && <Link to="/login" className="btn btn-secondary">Sign In</Link>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AccessDeniedPage
