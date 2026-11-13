interface Named {
  name?: string
  translations?: Array<{ language?: string; name?: string }>
  address_line1?: string
  city?: string
}

/** Adamlar kóretuǵın at: inglizsha awdarma, bolmasa qálegen awdarma, bolmasa `name`, bolmasa mánzil */
export function propertyDisplayName(property: Named): string {
  const translations = (property.translations ?? []).filter(t => t.name)
  return (
    translations.find(t => t.language === 'en')?.name ||
    translations[0]?.name ||
    property.name ||
    [property.address_line1, property.city].filter(Boolean).join(', ')
  )
}
