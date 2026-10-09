import type { FlagComponent } from 'country-flag-icons/react/3x2'
import {
  UZ, KZ, KG, TJ, TM, AF, RU, AM, AT, AZ, BY, BG, BR, CN, CZ, EG, FR, GE, DE, IN, ID, IR, IL, IT, JP, KW, MY, NL, PK, PL, QA, KR, SA, SG, ES, SE, CH, TH, TR, UA, AE, GB, US, VN,
} from 'country-flag-icons/react/3x2'
import type { PhoneCountryCode } from '../utils/phone'

// Flags are SVG components bundled with the app (no emoji, no image requests)
const FLAGS: Record<PhoneCountryCode, FlagComponent> = {
  UZ, KZ, KG, TJ, TM, AF, RU, AM, AT, AZ, BY, BG, BR, CN, CZ, EG, FR, GE, DE, IN, ID, IR, IL, IT, JP, KW, MY, NL, PK, PL, QA, KR, SA, SG, ES, SE, CH, TH, TR, UA, AE, GB, US, VN,
}

export function CountryFlag({ code }: { code: PhoneCountryCode }) {
  const Flag = FLAGS[code]
  return <Flag className="country-flag" width={20} height={14} aria-hidden="true" focusable="false" />
}
