import { SearchForm } from '../components/SearchForm'

// Mock data for homepage content
// TODO: Replace with real data from backend API when available
const FEATURED_DESTINATIONS = [
  { id: 1, name: 'Paris', country: 'France', image: '🗼', propertyCount: 1250 },
  { id: 2, name: 'Tokyo', country: 'Japan', image: '🗼', propertyCount: 980 },
  { id: 3, name: 'New York', country: 'USA', image: '🗽', propertyCount: 1100 },
  { id: 4, name: 'London', country: 'UK', image: '🏰', propertyCount: 890 },
]

const PROPERTY_TYPES = [
  { id: 1, name: 'Apartments', icon: '🏢', description: 'Modern city living spaces' },
  { id: 2, name: 'Houses', icon: '🏠', description: 'Spacious family homes' },
  { id: 3, name: 'Villas', icon: '🏡', description: 'Luxury vacation retreats' },
  { id: 4, name: 'Studios', icon: '🏙️', description: 'Compact urban spaces' },
]

const TESTIMONIALS = [
  {
    id: 1,
    name: 'Sarah Johnson',
    location: 'New York, USA',
    text: 'TICKBRON made finding our family vacation rental so easy. The property was exactly as described!',
    rating: 5,
  },
  {
    id: 2,
    name: 'Michael Chen',
    location: 'Singapore',
    text: 'Best platform for business travel. Always reliable and great customer service.',
    rating: 5,
  },
  {
    id: 3,
    name: 'Emma Wilson',
    location: 'London, UK',
    text: 'Found my dream apartment through TICKBRON. The verification process gave me peace of mind.',
    rating: 5,
  },
]

const STATS = [
  { value: '50K+', label: 'Properties Listed' },
  { value: '100K+', label: 'Happy Guests' },
  { value: '120+', label: 'Countries' },
  { value: '4.9', label: 'Average Rating' },
]

export function HomePage() {
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero" aria-label="Search for properties">
        <div className="hero-content">
          <h1 className="hero-title">Find Your Perfect Stay</h1>
          <p className="hero-subtitle">Discover unique homes and experiences around the world</p>
          <div className="hero-search">
            <SearchForm />
          </div>
          <div className="hero-stats" role="region" aria-label="Platform statistics">
            {STATS.map((stat) => (
              <div key={stat.label} className="hero-stat">
                <div className="hero-stat-value">{stat.value}</div>
                <div className="hero-stat-label">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Destinations */}
      <section className="destinations" aria-labelledby="destinations-title">
        <div className="container">
          <h2 id="destinations-title" className="section-title">Popular Destinations</h2>
          <p className="section-subtitle">Explore our most sought-after locations</p>
          <div className="destinations-grid" role="list">
            {FEATURED_DESTINATIONS.map((destination) => (
              <article key={destination.id} className="destination-card" role="listitem">
                <div className="destination-image" aria-hidden="true">{destination.image}</div>
                <div className="destination-info">
                  <h3 className="destination-name">{destination.name}</h3>
                  <p className="destination-country">{destination.country}</p>
                  <p className="destination-count">{destination.propertyCount} properties</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Property Types */}
      <section className="property-types" aria-labelledby="property-types-title">
        <div className="container">
          <h2 id="property-types-title" className="section-title">Property Types</h2>
          <p className="section-subtitle">Find the perfect accommodation for your needs</p>
          <div className="property-types-grid" role="list">
            {PROPERTY_TYPES.map((type) => (
              <article key={type.id} className="property-type-card" role="listitem">
                <div className="property-type-icon" aria-hidden="true">{type.icon}</div>
                <h3 className="property-type-name">{type.name}</h3>
                <p className="property-type-description">{type.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features" aria-labelledby="features-title">
        <div className="container">
          <h2 id="features-title" className="section-title">Why Choose TICKBRON?</h2>
          <p className="section-subtitle">Experience the difference with our premium service</p>
          <div className="features-grid" role="list">
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">✓</div>
              <h3 className="feature-title">Verified Properties</h3>
              <p className="feature-description">All properties are verified for quality and safety</p>
            </div>
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">🔒</div>
              <h3 className="feature-title">Secure Payments</h3>
              <p className="feature-description">Protected transactions with multiple payment options</p>
            </div>
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">🎧</div>
              <h3 className="feature-title">24/7 Support</h3>
              <p className="feature-description">Round-the-clock customer support for your peace of mind</p>
            </div>
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">⭐</div>
              <h3 className="feature-title">Best Price Guarantee</h3>
              <p className="feature-description">We match or beat any competitor's price</p>
            </div>
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">🌍</div>
              <h3 className="feature-title">Global Coverage</h3>
              <p className="feature-description">Properties available in 120+ countries</p>
            </div>
            <div className="feature-card" role="listitem">
              <div className="feature-icon" aria-hidden="true">📱</div>
              <h3 className="feature-title">Easy Booking</h3>
              <p className="feature-description">Book in minutes with our streamlined process</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials" aria-labelledby="testimonials-title">
        <div className="container">
          <h2 id="testimonials-title" className="section-title">What Our Guests Say</h2>
          <p className="section-subtitle">Real experiences from real travelers</p>
          <div className="testimonials-grid" role="list">
            {TESTIMONIALS.map((testimonial) => (
              <article key={testimonial.id} className="testimonial-card" role="listitem">
                <div className="testimonial-rating" aria-label={`Rating: ${testimonial.rating} out of 5 stars`}>
                  {'★'.repeat(testimonial.rating)}
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
                <div className="testimonial-author">
                  <div className="testimonial-name">{testimonial.name}</div>
                  <div className="testimonial-location">{testimonial.location}</div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta" aria-labelledby="cta-title">
        <div className="container">
          <div className="cta-content">
            <h2 id="cta-title" className="cta-title">Ready to Start Your Journey?</h2>
            <p className="cta-subtitle">Join millions of travelers who trust TICKBRON for their accommodations</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large">Browse Properties</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage
