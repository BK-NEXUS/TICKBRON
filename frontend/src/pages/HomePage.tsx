export function HomePage() {
  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-content">
          <h2>Find Your Perfect Stay</h2>
          <p>Discover unique homes and experiences around the world</p>
          <div className="hero-search">
            <input type="text" placeholder="Where are you going?" className="search-input" />
            <button className="btn btn-primary btn-large">Search</button>
          </div>
        </div>
      </section>
      
      <section className="features">
        <div className="container">
          <h3>Why Choose TICKBRON?</h3>
          <div className="features-grid">
            <div className="feature-card">
              <h4>Verified Properties</h4>
              <p>All properties are verified for quality and safety</p>
            </div>
            <div className="feature-card">
              <h4>Secure Payments</h4>
              <p>Protected transactions with multiple payment options</p>
            </div>
            <div className="feature-card">
              <h4>24/7 Support</h4>
              <p>Round-the-clock customer support for your peace of mind</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
