import { act } from '@testing-library/react'

/**
 * Let the requests a component starts on mount (mocked, so already resolved) finish and
 * update the component inside act(). Use it in tests that only check what renders first,
 * so the loaded data does not arrive after the test has ended.
 */
export async function settle() {
  await act(async () => {})
}
