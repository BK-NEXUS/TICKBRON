import type { I18nValue } from '../i18n/I18nContext'

type Field = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
type Translate = I18nValue['t']

export interface FormProblem {
  message: string
  field: Field
}

const isField = (element: Element): element is Field =>
  element instanceof HTMLInputElement || element instanceof HTMLSelectElement || element instanceof HTMLTextAreaElement

/** Iye maydan janında ne kóredi: májbúriy juldızsız yamasa eki noqatsız belgisi, bolmasa aria-label, bolmasa name */
function nameOf(field: Field): string {
  const label = field.labels?.[0]?.textContent ?? field.getAttribute('aria-label') ?? field.name
  return label.replace(/\*/g, '').replace(/\s+/g, ' ').trim().replace(/[:：]$/, '').trim()
}

function messageFor(field: Field, t: Translate): string | null {
  const { validity } = field
  const name = nameOf(field)
  if (validity.valueMissing) return t('form.required', { field: name })
  if (validity.typeMismatch) return field.type === 'email' ? t('auth.errEmail') : t('form.invalid', { field: name })
  if (validity.badInput) return t('form.number', { field: name })
  if (validity.rangeUnderflow) return t('form.min', { field: name, min: (field as HTMLInputElement).min })
  if (validity.rangeOverflow) return t('form.max', { field: name, max: (field as HTMLInputElement).max })
  // Brauzer uzınlıqtı tek paydalanıwshı tergen tekst ushın belgileydi, sol sebepli mánis usı jerde ólshenedi
  const { value } = field as HTMLInputElement
  const min = Number(field.getAttribute('minlength'))
  const max = field.getAttribute('maxlength')
  if (value && min > 0 && value.length < min) return t('form.minLength', { field: name, min })
  if (max !== null && value.length > Number(max)) return t('form.maxLength', { field: name, max })
  if (!validity.valid) return t('form.invalid', { field: name })
  return null
}

/**
 * Formanıń kirisiwleri belgilegen qaǵıydanı (required, type, min, max, length, pattern) buzatuǵın birinshi maydan (bet
 * tártibinde),
 * brauzerdiń óz tilinde emes, bet tilinde jazılǵan.
 */
export function firstFormProblem(form: HTMLFormElement, t: Translate): FormProblem | null {
  for (const element of Array.from(form.elements)) {
    if (!isField(element) || !element.willValidate) continue
    const message = messageFor(element, t)
    if (message) return { message, field: element }
  }
  return null
}

/**
 * `noValidate` formanıń submit handler inde birinshi shaqırıń: forma jiberiliwi múmkin bolsa true. Bolmasa
 * mashqala `report` ke baradı, maydan fokus alıp, handler toqtawı kerek.
 */
export function formAccepts(form: HTMLFormElement, t: Translate, report: (message: string) => void): boolean {
  const problem = firstFormProblem(form, t)
  if (!problem) return true
  report(problem.message)
  problem.field.focus()
  return false
}
