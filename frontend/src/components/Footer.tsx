export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-section">
          <h3>TICKBRON</h3>
          <p>Your trusted short-term rental platform</p>
        </div>
        <div className="footer-section">
          <h4>Explore</h4>
          <ul>
            <li><a href="/properties">Properties</a></li>
            <li><a href="/destinations">Destinations</a></li>
            <li><a href="/experiences">Experiences</a></li>
          </ul>
        </div>
        <div className="footer-section">
          <h4>Support</h4>
          <ul>
            <li><a href="/help">Help Center</a></li>
            <li><a href="/contact">Contact Us</a></li>
            <li><a href="/safety">Safety</a></li>
          </ul>
        </div>
        <div className="footer-section">
          <h4>Legal</h4>
          <ul>
            <li><a href="/terms">Terms of Service</a></li>
            <li><a href="/privacy">Privacy Policy</a></li>
            <li><a href="/cookies">Cookie Policy</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; 2024 TICKBRON. All rights reserved.</p>
      </div>
    </footer>
  )
}
