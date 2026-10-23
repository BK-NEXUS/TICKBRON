import { act, fireEvent, screen } from '@testing-library/react'

/**
 * Let the requests a component starts on mount (mocked, so already resolved) finish and
 * update the component inside act(). Use it in tests that only check what renders first,
 * so the loaded data does not arrive after the test has ended.
 */
export async function settle() {
  await act(async () => {})
}

/** Fill the first step's hotel name (English), which the wizard requires before "Next". */
export function nameTheHotel(name = 'Test Hotel') {
  fireEvent.change(screen.getByLabelText('Hotel name (English)'), { target: { value: name } })
}
