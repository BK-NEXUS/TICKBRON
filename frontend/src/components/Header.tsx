export function Header() {
  return (
    <header className="header">
      <div className="header-container">
        <div className="header-logo">
          <h1>TICKBRON</h1>
        </div>
        <nav className="header-nav">
          <a href="/" className="nav-link">Home</a>
          <a href="/properties" className="nav-link">Properties</a>
          <a href="/about" className="nav-link">About</a>
        </nav>
        <div className="header-actions">
          <button className="btn btn-secondary">Login</button>
          <button className="btn btn-primary">Sign Up</button>
        </div>
      </div>
    </header>
  )
}
