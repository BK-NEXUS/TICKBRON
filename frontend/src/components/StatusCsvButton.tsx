import { textKeys, useTexts } from '../i18n/I18nContext'
import { useState } from 'react'
import type { CsvFile, StatusResponse } from '../adapters/statusAdapter'
import { saveBlob } from '../utils/saveBlob'

interface StatusCsvButtonProps {
  onExport: () => Promise<StatusResponse<CsvFile>>
}

const TEXT_KEYS = textKeys({ export: 'status.exportCsv', exporting: 'status.exporting' })

/** Downloads a Status CSV through the authenticated adapter and shows why it failed */
export function StatusCsvButton({ onExport }: StatusCsvButtonProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setBusy(true)
    setError(null)
    const { data, error: message } = await onExport()
    setBusy(false)
    if (data) saveBlob(data.blob, data.filename)
    else setError(message)
  }

  return (
    <div className="status-csv">
      <button type="button" className="btn btn-secondary" onClick={handleClick} disabled={busy}>
        {busy ? TEXT.exporting : TEXT.export}
      </button>
      {error && <p role="alert" className="status-range-error">{error}</p>}
    </div>
  )
}
