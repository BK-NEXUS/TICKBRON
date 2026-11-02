export type Certificate = {
  id: string
  name: string
  score: string
  year: number
  issuer: string
}

export type SocialLink = {
  id: 'telegram' | 'instagram' | 'linkedin' | 'email'
  label: string
  href: string
}

export type Profile = {
  firstName: string
  lastName: string
  website: { url: string; label: string }
  certificates: Certificate[]
  socials: SocialLink[]
  stats: { id: 'experience' | 'students' | 'certificates'; value: number }[]
}

// Sample data: replace with the client's real details when they arrive.
export const profile: Profile = {
  firstName: 'Aziza',
  lastName: 'Karimova',
  website: { url: 'https://example.com', label: 'example.com' },
  certificates: [
    { id: 'ielts', name: 'IELTS Academic', score: '8.0', year: 2024, issuer: 'British Council' },
    { id: 'cefr', name: 'CEFR English', score: 'C2', year: 2023, issuer: 'Cambridge Assessment' },
    { id: 'toefl', name: 'TOEFL iBT', score: '112', year: 2023, issuer: 'ETS' },
    { id: 'cae', name: 'Cambridge CAE', score: 'A', year: 2022, issuer: 'Cambridge English' },
    { id: 'torfl', name: 'TORFL', score: 'C1', year: 2022, issuer: 'RUDN University' },
  ],
  socials: [
    { id: 'telegram', label: 'Telegram', href: 'https://t.me/example' },
    { id: 'instagram', label: 'Instagram', href: 'https://instagram.com/example' },
    { id: 'linkedin', label: 'LinkedIn', href: 'https://linkedin.com/in/example' },
    { id: 'email', label: 'Email', href: 'mailto:hello@example.com' },
  ],
  stats: [
    { id: 'experience', value: 7 },
    { id: 'students', value: 350 },
    { id: 'certificates', value: 5 },
  ],
}
