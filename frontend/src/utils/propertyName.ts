interface Named {
  name?: string
  translations?: Array<{ language?: string; name?: string }>
  address_line1?: string
  city?: string
}

/** The name people see: English translation, else any translation, else `name`, else the address */
export function propertyDisplayName(property: Named): string {
  const translations = (property.translations ?? []).filter(t => t.name)
  return (
    translations.find(t => t.language === 'en')?.name ||
    translations[0]?.name ||
    property.name ||
    [property.address_line1, property.city].filter(Boolean).join(', ')
  )
}
