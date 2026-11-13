import { useI18n } from '../i18n/I18nContext'
import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router'
import { DateRangeCalendar } from './DateRangeCalendar'
import { keepFilterParams } from '../utils/searchFilters'
import { businessToday } from '../utils/dates'

// Izlew forması jaǵdayı interface i
export interface SearchFormData {
  destination: string
  checkIn: string
  checkOut: string
  guests: number
  adults: number
  children: number
  rooms: number
}

// Validation qátelikleri interface i
export interface SearchFormErrors {
  destination?: string
  checkIn?: string
  checkOut?: string
  guests?: string
  adults?: string
  children?: string
  rooms?: string
}

// Ádetdegi forma mánisleri
const DEFAULT_VALUES: SearchFormData = {
  destination: '',
  checkIn: '',
  checkOut: '',
  guests: 1,
  adults: 1,
  children: 0,
  rooms: 1,
}

// URL parametr atları
const URL_PARAMS = {
  DESTINATION: 'destination',
  CHECK_IN: 'check_in',
  CHECK_OUT: 'check_out',
  GUESTS: 'guests',
  ADULTS: 'adults',
  CHILDREN: 'children',
  ROOMS: 'rooms',
}

/**
 * URL jaǵdayı sinxronizaciyası menen SearchForm komponenti
 * Izlew parametrlerin URL query parametrleri arqalı isleydi:
 * - Bólisiwge bolatuǵın izlew URL leri
 * - Brauzerdi jańalaǵanda saqlanıw
 * - Brauzer artqa/aldıǵa navigaciyası
 */
export function SearchForm() {
  const { t } = useI18n()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  
  const [formData, setFormData] = useState<SearchFormData>(DEFAULT_VALUES)
  const [errors, setErrors] = useState<SearchFormErrors>({})
  const [touched, setTouched] = useState<Set<keyof SearchFormData>>(new Set())
  const [calendarOpen, setCalendarOpen] = useState(false)

  // Aralıq kalendarı: birinshi klik check-in, ekinshisi check-out
  const handleRangeChange = (checkIn: string | null, checkOut: string | null) => {
    setFormData(prev => ({ ...prev, checkIn: checkIn ?? '', checkOut: checkOut ?? '' }))
    setErrors(prev => ({ ...prev, checkIn: undefined, checkOut: undefined }))
    if (checkIn && checkOut) setCalendarOpen(false)
  }

  // Ornatılǵanda formanı URL parametrlerinen baslaw
  useEffect(() => {
    const urlDestination = searchParams.get(URL_PARAMS.DESTINATION)
    const urlCheckIn = searchParams.get(URL_PARAMS.CHECK_IN)
    const urlCheckOut = searchParams.get(URL_PARAMS.CHECK_OUT)
    const urlGuests = searchParams.get(URL_PARAMS.GUESTS)
    const urlAdults = searchParams.get(URL_PARAMS.ADULTS)
    const urlChildren = searchParams.get(URL_PARAMS.CHILDREN)
    const urlRooms = searchParams.get(URL_PARAMS.ROOMS)

    setFormData({
      destination: urlDestination || DEFAULT_VALUES.destination,
      checkIn: urlCheckIn || DEFAULT_VALUES.checkIn,
      checkOut: urlCheckOut || DEFAULT_VALUES.checkOut,
      guests: urlGuests && !isNaN(parseInt(urlGuests, 10)) ? parseInt(urlGuests, 10) : DEFAULT_VALUES.guests,
      adults: urlAdults && !isNaN(parseInt(urlAdults, 10)) ? parseInt(urlAdults, 10) : DEFAULT_VALUES.adults,
      children: urlChildren && !isNaN(parseInt(urlChildren, 10)) ? parseInt(urlChildren, 10) : DEFAULT_VALUES.children,
      rooms: urlRooms && !isNaN(parseInt(urlRooms, 10)) ? parseInt(urlRooms, 10) : DEFAULT_VALUES.rooms,
    })
  }, [searchParams])

  // Forma maǵlıwmatın tekseriw
  const validateForm = (data: SearchFormData): SearchFormErrors => {
    const newErrors: SearchFormErrors = {}

    // Barar orındı tekseriw
    if (!data.destination.trim()) {
      newErrors.destination = t('searchForm.error.destinationRequired')
    } else if (data.destination.length < 2) {
      newErrors.destination = t('searchForm.error.destinationShort')
    } else if (data.destination.length > 100) {
      newErrors.destination = t('searchForm.error.destinationLong')
    }

    // Sanalar ıqtıyarıy (tek qala boyınsha izlew), biraq aralıqtıń eki ushı da kerek
    if (!data.checkIn && data.checkOut) {
      newErrors.checkIn = t('searchForm.error.checkInRequired')
    } else if (data.checkIn) {
      if (data.checkIn < businessToday()) {
        newErrors.checkIn = t('searchForm.error.checkInPast')
      }
    }

    // Check-out sanasın tekseriw
    if (!data.checkOut && data.checkIn) {
      newErrors.checkOut = t('searchForm.error.checkOutRequired')
    } else if (data.checkOut && data.checkIn) {
      const checkInDate = new Date(data.checkIn)
      const checkOutDate = new Date(data.checkOut)
      
      if (checkOutDate <= checkInDate) {
        newErrors.checkOut = t('searchForm.error.checkOutOrder')
      }
    }

    // Mehmanlardı tekseriw
    if (data.guests < 1) {
      newErrors.guests = t('searchForm.error.guestsMin')
    } else if (data.guests > 50) {
      newErrors.guests = t('searchForm.error.guestsMax')
    }

    // Úlken adamlardı tekseriw
    if (data.adults < 1) {
      newErrors.adults = t('searchForm.error.adultsMin')
    } else if (data.adults > 50) {
      newErrors.adults = t('searchForm.error.adultsMax')
    }

    // Balalardı tekseriw
    if (data.children < 0) {
      newErrors.children = t('searchForm.error.childrenNegative')
    } else if (data.children > 20) {
      newErrors.children = t('searchForm.error.childrenMax')
    }

    // Xonalardı tekseriw
    if (data.rooms < 1) {
      newErrors.rooms = t('searchForm.error.roomsMin')
    } else if (data.rooms > 20) {
      newErrors.rooms = t('searchForm.error.roomsMax')
    }

    // Mehmanlar quramın tekseriw
    if (data.adults + data.children !== data.guests) {
      newErrors.guests = t('searchForm.error.guestsTotal')
    }

    return newErrors
  }

  // Kirisiw ózgeriwin islew
  const handleChange = (field: keyof SearchFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Paydalanıwshı teriwdi baslaǵanda usı maydan ushın qátelikti tazalaw
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  // Maydan blur ın islew (blur da tekseriw ushın)
  const handleBlur = (field: keyof SearchFormData) => {
    setTouched(prev => new Set(prev).add(field))
    const fieldErrors = validateForm(formData)
    if (fieldErrors[field]) {
      setErrors(prev => ({ ...prev, [field]: fieldErrors[field] }))
    }
  }

  // Forma jiberiwin islew
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Barlıq maydanlardı tekseriw
    const validationErrors = validateForm(formData)
    setErrors(validationErrors)
    
    // Barlıq maydanlardı tiyilgen dep belgilew
    setTouched(new Set(Object.keys(DEFAULT_VALUES) as Array<keyof SearchFormData>))
    
    // Qátelik bolsa jibermew
    if (Object.keys(validationErrors).length > 0) {
      return
    }

    // URL parametrlerin jańalaw
    const newParams = new URLSearchParams()
    
    if (formData.destination) {
      newParams.set(URL_PARAMS.DESTINATION, formData.destination)
    }
    if (formData.checkIn) {
      newParams.set(URL_PARAMS.CHECK_IN, formData.checkIn)
    }
    if (formData.checkOut) {
      newParams.set(URL_PARAMS.CHECK_OUT, formData.checkOut)
    }
    newParams.set(URL_PARAMS.GUESTS, formData.guests.toString())
    newParams.set(URL_PARAMS.ADULTS, formData.adults.toString())
    newParams.set(URL_PARAMS.CHILDREN, formData.children.toString())
    newParams.set(URL_PARAMS.ROOMS, formData.rooms.toString())
    // Nátiyjeler betinen qayta izlew jan panel filterlerin hám tártipti saqlaydı
    keepFilterParams(searchParams, newParams)

    // Parametrler menen izlew nátiyjeleri betine ótiw
    navigate(`/search?${newParams.toString()}`)
  }

  // Maydanǵa tiyisli ózgeris handler lerin islew
  const handleDestinationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange('destination', e.target.value)
  }

  const handleCheckInChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange('checkIn', e.target.value)
  }

  const handleCheckOutChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange('checkOut', e.target.value)
  }

  const handleGuestsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10) || 0
    handleChange('guests', value)
  }

  const handleAdultsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10) || 0
    handleChange('adults', value)
  }

  const handleChildrenChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10) || 0
    handleChange('children', value)
  }

  const handleRoomsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10) || 0
    handleChange('rooms', value)
  }

  return (
    <form className="search-form" onSubmit={handleSubmit} noValidate>
      <div className="search-form-grid">
        {/* Barar orın */}
        <div className="search-form-field">
          <label htmlFor="destination" className="search-form-label">
            {t('searchForm.destination')}
          </label>
          <input
            id="destination"
            type="text"
            className={`search-form-input ${errors.destination && touched.has('destination') ? 'search-form-input-error' : ''}`}
            placeholder={t('searchForm.destinationPlaceholder')}
            value={formData.destination}
            onChange={handleDestinationChange}
            onBlur={() => handleBlur('destination')}
            aria-invalid={errors.destination && touched.has('destination') ? 'true' : 'false'}
            aria-describedby={errors.destination && touched.has('destination') ? 'destination-error' : undefined}
          />
          {errors.destination && touched.has('destination') && (
            <span id="destination-error" className="search-form-error" role="alert">
              {errors.destination}
            </span>
          )}
        </div>

        {/* Kiriw sanası */}
        <div className="search-form-field">
          <label htmlFor="checkIn" className="search-form-label">
            {t('searchForm.checkIn')}
          </label>
          <input
            id="checkIn"
            type="date"
            className={`search-form-input ${errors.checkIn && touched.has('checkIn') ? 'search-form-input-error' : ''}`}
            value={formData.checkIn}
            onChange={handleCheckInChange}
            onClick={() => setCalendarOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={calendarOpen}
            onBlur={() => handleBlur('checkIn')}
            aria-invalid={errors.checkIn && touched.has('checkIn') ? 'true' : 'false'}
            aria-describedby={errors.checkIn && touched.has('checkIn') ? 'checkIn-error' : undefined}
          />
          {errors.checkIn && touched.has('checkIn') && (
            <span id="checkIn-error" className="search-form-error" role="alert">
              {errors.checkIn}
            </span>
          )}
        </div>

        {/* Shıǵıw sanası */}
        <div className="search-form-field">
          <label htmlFor="checkOut" className="search-form-label">
            {t('searchForm.checkOut')}
          </label>
          <input
            id="checkOut"
            type="date"
            className={`search-form-input ${errors.checkOut && touched.has('checkOut') ? 'search-form-input-error' : ''}`}
            value={formData.checkOut}
            onChange={handleCheckOutChange}
            onClick={() => setCalendarOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={calendarOpen}
            onBlur={() => handleBlur('checkOut')}
            aria-invalid={errors.checkOut && touched.has('checkOut') ? 'true' : 'false'}
            aria-describedby={errors.checkOut && touched.has('checkOut') ? 'checkOut-error' : undefined}
          />
          {errors.checkOut && touched.has('checkOut') && (
            <span id="checkOut-error" className="search-form-error" role="alert">
              {errors.checkOut}
            </span>
          )}
        </div>

        {calendarOpen && (
          <div className="search-form-calendar" role="dialog" aria-label={t('searchForm.chooseDates')}>
            <div className="search-form-calendar-header">
              <span className="search-form-calendar-hint">
                {!formData.checkIn || formData.checkOut ? t('searchForm.hintCheckIn') : t('searchForm.hintCheckOut')}
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={() => setCalendarOpen(false)}
                aria-label={t('searchForm.closeCalendar')}
              >
                ✕
              </button>
            </div>
            <DateRangeCalendar
              checkIn={formData.checkIn || null}
              checkOut={formData.checkOut || null}
              onChange={handleRangeChange}
            />
          </div>
        )}

        {/* Mehmanlar */}
        <div className="search-form-field">
          <label htmlFor="guests" className="search-form-label">
            {t('searchForm.guests')}
          </label>
          <input
            id="guests"
            type="number"
            min="1"
            max="50"
            className={`search-form-input ${errors.guests && touched.has('guests') ? 'search-form-input-error' : ''}`}
            value={formData.guests}
            onChange={handleGuestsChange}
            onBlur={() => handleBlur('guests')}
            aria-invalid={errors.guests && touched.has('guests') ? 'true' : 'false'}
            aria-describedby={errors.guests && touched.has('guests') ? 'guests-error' : undefined}
          />
          {errors.guests && touched.has('guests') && (
            <span id="guests-error" className="search-form-error" role="alert">
              {errors.guests}
            </span>
          )}
        </div>

        {/* Úlken adamlar */}
        <div className="search-form-field">
          <label htmlFor="adults" className="search-form-label">
            {t('searchForm.adults')}
          </label>
          <input
            id="adults"
            type="number"
            min="1"
            max="50"
            className={`search-form-input ${errors.adults && touched.has('adults') ? 'search-form-input-error' : ''}`}
            value={formData.adults}
            onChange={handleAdultsChange}
            onBlur={() => handleBlur('adults')}
            aria-invalid={errors.adults && touched.has('adults') ? 'true' : 'false'}
            aria-describedby={errors.adults && touched.has('adults') ? 'adults-error' : undefined}
          />
          {errors.adults && touched.has('adults') && (
            <span id="adults-error" className="search-form-error" role="alert">
              {errors.adults}
            </span>
          )}
        </div>

        {/* Balalar */}
        <div className="search-form-field">
          <label htmlFor="children" className="search-form-label">
            {t('searchForm.children')}
          </label>
          <input
            id="children"
            type="number"
            min="0"
            max="20"
            className={`search-form-input ${errors.children && touched.has('children') ? 'search-form-input-error' : ''}`}
            value={formData.children}
            onChange={handleChildrenChange}
            onBlur={() => handleBlur('children')}
            aria-invalid={errors.children && touched.has('children') ? 'true' : 'false'}
            aria-describedby={errors.children && touched.has('children') ? 'children-error' : undefined}
          />
          {errors.children && touched.has('children') && (
            <span id="children-error" className="search-form-error" role="alert">
              {errors.children}
            </span>
          )}
        </div>

        {/* Xonalar */}
        <div className="search-form-field">
          <label htmlFor="rooms" className="search-form-label">
            {t('searchForm.rooms')}
          </label>
          <input
            id="rooms"
            type="number"
            min="1"
            max="20"
            className={`search-form-input ${errors.rooms && touched.has('rooms') ? 'search-form-input-error' : ''}`}
            value={formData.rooms}
            onChange={handleRoomsChange}
            onBlur={() => handleBlur('rooms')}
            aria-invalid={errors.rooms && touched.has('rooms') ? 'true' : 'false'}
            aria-describedby={errors.rooms && touched.has('rooms') ? 'rooms-error' : undefined}
          />
          {errors.rooms && touched.has('rooms') && (
            <span id="rooms-error" className="search-form-error" role="alert">
              {errors.rooms}
            </span>
          )}
        </div>

        {/* Jiberiw túymesi */}
        <div className="search-form-field search-form-submit">
          <button type="submit" className="btn btn-primary btn-large">
            {t('searchForm.search')}
          </button>
        </div>
      </div>
    </form>
  )
}