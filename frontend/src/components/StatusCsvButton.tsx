import { textKeys, useTexts } from '../i18n/I18nContext'
import { useState } from 'react'
import type { CsvFile, ExportFormat, StatusResponse } from '../adapters/statusAdapter'
import { saveBlob } from '../utils/saveBlob'

interface StatusCsvButtonProps {
  onExport: (format: ExportFormat) => Promise<StatusResponse<CsvFile>>
}

const TEXT_KEYS = textKeys({ export: 'status.exportCsv', exportExcel: 'status.exportExcel', exporting: 'status.exporting' })

/** Downloads a Status CSV or Excel file through the authenticated adapter and shows why it failed */
export function StatusCsvButton({ onExport }: StatusCsvButtonProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const [busy, setBusy] = useState<ExportFormat | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async (format: ExportFormat) => {
    setBusy(format)
    setError(null)
    const { data, error: message } = await onExport(format)
    setBusy(null)
    if (data) saveBlob(data.blob, data.filename)
    else setError(message)
  }

  return (
    <div className="status-csv">
      <div className="status-csv-buttons">
        <button type="button" className="btn btn-secondary" onClick={() => handleClick('csv')} disabled={busy !== null}>
          {busy === 'csv' ? TEXT.exporting : TEXT.export}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => handleClick('xlsx')} disabled={busy !== null}>
          {busy === 'xlsx' ? TEXT.exporting : TEXT.exportExcel}
        </button>
      </div>
      {error && <p role="alert" className="status-range-error">{error}</p>}
    </div>
  )
}
