import { Link } from 'react-router-dom'

/**
 * Static information pages linked from the header and footer.
 * The legal texts are short plain-language summaries; they need a review
 * before a public launch.
 */
export type InfoPageSlug = 'about' | 'help' | 'contact' | 'safety' | 'terms' | 'privacy' | 'cookies'

interface Section {
  heading: string
  body: string
}

const PAGES: Record<InfoPageSlug, { title: string; intro: string; sections: Section[] }> = {
  about: {
    title: 'About TICKBRON',
    intro: 'TICKBRON is an online booking platform for hotels and guesthouses in Uzbekistan and Central Asia.',
    sections: [
      { heading: 'What we do', body: 'Guests search stays by city and dates, see the real price for every night before booking, and pay online. Hotel owners manage their rooms, rates and availability in the partner panel.' },
      { heading: 'Verified properties', body: 'Every property is checked and approved by our team before it appears in search.' },
    ],
  },
  help: {
    title: 'Help Center',
    intro: 'Answers to the most common questions about booking with TICKBRON.',
    sections: [
      { heading: 'How do I book a stay?', body: 'Search for a city, open a property, choose a room and rate, pick your check-in and check-out dates in the calendar and continue to booking and payment.' },
      { heading: 'Where can I see my bookings?', body: 'Log in and open "My Bookings" from the menu. Each booking has a reference code you can give to our support team.' },
      { heading: 'Can I cancel a booking?', body: 'Open the booking in "My Bookings". The cancellation terms of the rate you booked apply.' },
      { heading: 'I did not receive my login code', body: 'Check that your phone number is in international format, e.g. +998 90 123 45 67, and request a new code after a minute.' },
    ],
  },
  contact: {
    title: 'Contact Us',
    intro: 'Our support team helps guests and hotel owners with bookings, payments and accounts.',
    sections: [
      { heading: 'Bookings and payments', body: 'Have your booking reference code ready (6 letters and digits, shown on the confirmation page and in "My Bookings").' },
      { heading: 'Hotel owners', body: 'Accounts for hotel owners are created by the TICKBRON team. Contact us to list your property.' },
    ],
  },
  safety: {
    title: 'Safety',
    intro: 'How we keep your stay and your account safe.',
    sections: [
      { heading: 'Secure payments', body: 'Payments go through licensed payment providers. TICKBRON never asks for your card details by phone or message.' },
      { heading: 'Your account', body: 'Never share your login code. Our team will never ask you for it.' },
      { heading: 'Verified properties', body: 'Properties are approved by our team before guests can book them.' },
    ],
  },
  terms: {
    title: 'Terms of Service',
    intro: 'A short summary of the rules for using TICKBRON.',
    sections: [
      { heading: 'Bookings', body: 'A booking is an agreement between the guest and the property. The price shown before payment is the price you pay; the rate you choose sets the cancellation terms.' },
      { heading: 'Accounts', body: 'You are responsible for the details you enter and for keeping your login code private.' },
      { heading: 'Properties', body: 'Hotel owners are responsible for keeping their descriptions, prices and availability correct.' },
    ],
  },
  privacy: {
    title: 'Privacy Policy',
    intro: 'What personal data TICKBRON keeps and why.',
    sections: [
      { heading: 'What we collect', body: 'Your name, email address, phone number and your bookings, so that properties can receive your reservation and we can support you.' },
      { heading: 'Who sees it', body: 'The property you book sees the guest details of that booking. Payment providers receive what they need to process the payment.' },
      { heading: 'Your choices', body: 'You can update your profile at any time. Contact us to delete your account.' },
    ],
  },
  cookies: {
    title: 'Cookie Policy',
    intro: 'TICKBRON uses only the cookies it needs to work.',
    sections: [
      { heading: 'Session cookie', body: 'Keeps you logged in while you browse.' },
      { heading: 'Security cookie', body: 'Protects forms against cross-site request forgery (CSRF).' },
      { heading: 'Preferences', body: 'Some settings, such as dismissed tips, are kept in your browser storage.' },
    ],
  },
}

export function InfoPage({ slug }: { slug: InfoPageSlug }) {
  const page = PAGES[slug]
  return (
    <div className="info-page container">
      <h1 className="info-page-title">{page.title}</h1>
      <p className="info-page-intro">{page.intro}</p>
      {page.sections.map(section => (
        <section key={section.heading} className="info-page-section">
          <h2>{section.heading}</h2>
          <p>{section.body}</p>
        </section>
      ))}
      <p className="info-page-footer">
        <Link to="/search" className="btn btn-primary">Browse properties</Link>
      </p>
    </div>
  )
}

export default InfoPage
