export const OTHER_LETTER = '#'

/** `name` `letter` astına kire me ('' = hámmesi, '#' = háripten baslanbaytuǵın at)? Serverdegi birdey qaǵıyda. */
export function nameMatchesLetter(name: string, letter: string): boolean {
  if (!letter) return true
  const first = name.trim().charAt(0)
  if (letter === OTHER_LETTER) return first !== '' && first.toLocaleUpperCase() === first.toLocaleLowerCase()
  return first.toLocaleUpperCase() === letter.toLocaleUpperCase()
}
