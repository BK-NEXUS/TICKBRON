export const OTHER_LETTER = '#'

/** Does `name` belong under `letter` ('' = all, '#' = a name that does not start with a letter)? Same rule as the server. */
export function nameMatchesLetter(name: string, letter: string): boolean {
  if (!letter) return true
  const first = name.trim().charAt(0)
  if (letter === OTHER_LETTER) return first !== '' && first.toLocaleUpperCase() === first.toLocaleLowerCase()
  return first.toLocaleUpperCase() === letter.toLocaleUpperCase()
}
