import type { MessageKey } from '../i18n/messages/en'
import { useI18n } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { useDialogFocus } from '../hooks/useDialogFocus'
import {
  partnerAdapter, PartnerRoomInventory, PartnerBlock,
} from '../adapters/partnerAdapter'
import { DateRangeCalendar } from './DateRangeCalendar'
import { addDays, nightsBetween, toLocalDate } from '../utils/dates'

interface PartnerRoomCalendarProps {
  roomTypeId: number
  roomTypeName: string
  totalRooms: number
  /** YYYY-MM shown first; defaults to the current month. A testing seam. */
  initialMonth?: string
}

type Status = 'free' | 'partly-sold' | 'full' | 'closed'

const STATUS_COLOR: Record<Status, string> = {
  free: 'var(--color-success)',
  'partly-sold': 'var(--color-warning)',
  full: 'var(--color-error)',
  closed: 'var(--color-text-tertiary)',
}

const STATUS_LABEL: Record<Status, MessageKey> = {
  free: 'partner.statusFree',
  'partly-sold': 'partner.statusPartlySold',
  full: 'partner.statusFull',
  closed: 'partner.statusClosed',
}

/** How far ahead room inventory and blocks are fetched in one shot. */
const WINDOW_DAYS = 180

function statusOf(row: PartnerRoomInventory | undefined, totalRooms: number): Status {
  const isOpen = row?.is_available ?? true
  if (!isOpen) return 'closed'
  const remaining = row ? row.remaining_rooms : totalRooms
  const available = row ? row.available_rooms : totalRooms
  if (remaining <= 0) return 'full'
  if (remaining < available) return 'partly-sold'
  return 'free'
}

/**
 * Owner calendar for one room type (3.6): a month grid showing free X of Y and a color
 * per day, a panel to edit one day or a date range (available rooms, open/closed), and
 * external-booking blocks (rooms sold outside TICKBRON) shown on the calendar and
 * removable. RoomInventory is shared by every rate plan of this room type, so this is
 * the room count that decides whether a room can still be sold (audit #31).
 */
export function PartnerRoomCalendar({ roomTypeId, roomTypeName, totalRooms, initialMonth }: PartnerRoomCalendarProps) {
  const { t, formatDay } = useI18n()
  const [rows, setRows] = useState<PartnerRoomInventory[]>([])
  const [blocks, setBlocks] = useState<PartnerBlock[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const [checkIn, setCheckIn] = useState<string | null>(null)
  const [checkOut, setCheckOut] = useState<string | null>(null)
  const [editAvailable, setEditAvailable] = useState(totalRooms)
  const [editOpen, setEditOpen] = useState(true)
  const [saving, setSaving] = useState(false)

  const [blockModalOpen, setBlockModalOpen] = useState(false)
  const [blockDateFrom, setBlockDateFrom] = useState('')
  const [blockDateTo, setBlockDateTo] = useState('')
  const [blockRooms, setBlockRooms] = useState(1)
  const [blockNote, setBlockNote] = useState('')
  const [blockSaving, setBlockSaving] = useState(false)
  const [blockError, setBlockError] = useState<string | null>(null)

  useEffect(() => {
    loadCalendarData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomTypeId])

  const loadCalendarData = async () => {
    setLoading(true)
    setError(null)
    const today = toLocalDate(new Date())
    const future = addDays(today, WINDOW_DAYS)
    const [inventoryResponse, blocksResponse] = await Promise.all([
      partnerAdapter.getRoomInventory({ room_type: roomTypeId, date_from: today, date_to: future }),
      partnerAdapter.getBlocks({ room_type: roomTypeId }),
    ])
    if (inventoryResponse.error) setError(inventoryResponse.error)
    else if (inventoryResponse.data) setRows(inventoryResponse.data)
    if (blocksResponse.error) setError((prev) => prev ?? blocksResponse.error)
    else if (blocksResponse.data) setBlocks(blocksResponse.data)
    setLoading(false)
  }

  const byDate = new Map(rows.map((row) => [row.date, row]))
  const blocksByDate = new Map<string, PartnerBlock[]>()
  for (const block of blocks) {
    for (const night of nightsBetween(block.date_from, block.date_to)) {
      const list = blocksByDate.get(night) ?? []
      list.push(block)
      blocksByDate.set(night, list)
    }
  }

  const clearSelection = () => {
    setCheckIn(null)
    setCheckOut(null)
  }

  const openPanelFor = (date: string, rangeEnd: string | null) => {
    setCheckIn(date)
    setCheckOut(rangeEnd)
    const row = byDate.get(date)
    setEditAvailable(row ? row.available_rooms : totalRooms)
    setEditOpen(row ? row.is_available : true)
    setSuccessMessage(null)
  }

  const handleRangeChange = (nextCheckIn: string | null, nextCheckOut: string | null) => {
    if (!nextCheckIn) {
      clearSelection()
      return
    }
    openPanelFor(nextCheckIn, nextCheckOut)
  }

  const handleSaveDay = async () => {
    if (!checkIn) return
    setSaving(true)
    setError(null)
    const existing = byDate.get(checkIn)
    const response = existing
      ? await partnerAdapter.updateRoomInventory(existing.id, { available_rooms: editAvailable, is_available: editOpen })
      : await partnerAdapter.createRoomInventory({
        room_type: roomTypeId, date: checkIn, available_rooms: editAvailable, is_available: editOpen,
      })
    if (response.error) {
      setError(response.error)
      setSaving(false)
      return
    }
    setSuccessMessage(t('partner.savedDay', { day: formatDay(checkIn) }))
    clearSelection()
    setSaving(false)
    await loadCalendarData()
  }

  const handleSaveRange = async () => {
    if (!checkIn || !checkOut) return
    setSaving(true)
    setError(null)
    const response = await partnerAdapter.bulkSetRoomInventory({
      room_type: roomTypeId, date_from: checkIn, date_to: checkOut,
      available_rooms: editAvailable, is_available: editOpen,
    })
    if (response.error) {
      setError(response.error)
      setSaving(false)
      return
    }
    setSuccessMessage(t('partner.savedRange', { from: formatDay(checkIn), to: formatDay(addDays(checkOut, -1)) }))
    clearSelection()
    setSaving(false)
    await loadCalendarData()
  }

  const openBlockModal = () => {
    setBlockDateFrom(checkIn ?? toLocalDate(new Date()))
    setBlockDateTo(checkOut ?? addDays(checkIn ?? toLocalDate(new Date()), 1))
    setBlockRooms(1)
    setBlockNote('')
    setBlockError(null)
    setBlockModalOpen(true)
  }

  const dialogRef = useDialogFocus<HTMLDivElement>(blockModalOpen, () => closeBlockModal())

  const closeBlockModal = () => {
    setBlockModalOpen(false)
    setBlockError(null)
  }

  const handleCreateBlock = async () => {
    setBlockSaving(true)
    setBlockError(null)
    const response = await partnerAdapter.createBlock({
      room_type: roomTypeId, date_from: blockDateFrom, date_to: blockDateTo,
      rooms: blockRooms, note: blockNote,
    })
    if (response.error) {
      setBlockError(response.error)
      setBlockSaving(false)
      return
    }
    setBlockSaving(false)
    setBlockModalOpen(false)
    setSuccessMessage(t('partner.externalBookingBlockCreated'))
    clearSelection()
    await loadCalendarData()
  }

  const handleRemoveBlock = async (block: PartnerBlock) => {
    if (!confirm(t('partner.confirmRemoveBlock', { note: block.note }))) return
    setError(null)
    const response = await partnerAdapter.deleteBlock(block.id)
    if (response.error) {
      setError(response.error)
      return
    }
    setSuccessMessage(t('partner.blockRemoved'))
    await loadCalendarData()
  }

  const isRange = Boolean(checkIn && checkOut)

  return (
    <div className="partner-room-calendar">
      <div className="partner-calendar-header">
        <h2 className="partner-calendar-title">{t('partner.calendarFor', { name: roomTypeName })}</h2>
        <button
          type="button"
          onClick={openBlockModal}
          className="btn btn-primary"
          aria-label={t('partner.externalFor', { name: roomTypeName })}
        >
          {t('partner.externalBooking')}
        </button>
      </div>

      {successMessage && (
        <div className="alert alert-success" role="alert" aria-live="polite">{successMessage}</div>
      )}
      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">{error}</div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">{t('partner.loadingCalendar')}</div>
      ) : (
        <div className="partner-calendar-body">
          <DateRangeCalendar
            checkIn={checkIn}
            checkOut={checkOut}
            onChange={handleRangeChange}
            initialMonth={initialMonth}
            describeDay={(date) => {
              const row = byDate.get(date)
              const status = statusOf(row, totalRooms)
              const remaining = row ? row.remaining_rooms : totalRooms
              const available = row ? row.available_rooms : totalRooms
              const dayBlocks = blocksByDate.get(date) ?? []
              return {
                selectable: true,
                status,
                content: (
                  <>
                    <div className="partner-calendar-day-count">{remaining} / {available}</div>
                    {dayBlocks.length > 0 && (
                      <div className="partner-calendar-day-block" title={dayBlocks.map((b) => b.note).join(', ')}>
                        {dayBlocks[0].note}
                      </div>
                    )}
                    <div
                      className="availability-calendar-day-indicator"
                      style={{ backgroundColor: STATUS_COLOR[status] }}
                      aria-hidden="true"
                    />
                  </>
                ),
              }
            }}
          >
            <div className="availability-calendar-legend">
              {(Object.keys(STATUS_LABEL) as Status[]).map((status) => (
                <div key={status} className="availability-calendar-legend-item">
                  <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR[status] }} />
                  <span>{t(STATUS_LABEL[status])}</span>
                </div>
              ))}
            </div>
          </DateRangeCalendar>

          {checkIn && (
            <div className="partner-calendar-day-panel" role="region" aria-label={t('partner.editDay')}>
              <h3 className="partner-calendar-day-panel-title">
                {isRange
                  ? t('partner.editingRange', { from: formatDay(checkIn), to: formatDay(addDays(checkOut as string, -1)) })
                  : t('partner.editingDay', { day: formatDay(checkIn) })}
              </h3>

              <div className="form-group">
                <label htmlFor="edit-available-rooms">{t('partner.availableRoomsOf', { total: totalRooms })}</label>
                <input
                  id="edit-available-rooms"
                  type="number"
                  min={0}
                  max={totalRooms}
                  value={editAvailable}
                  onChange={(e) => setEditAvailable(parseInt(e.target.value) || 0)}
                  className="form-input"
                />
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editOpen}
                    onChange={(e) => setEditOpen(e.target.checked)}
                  />
                  <span>{t('partner.openForBooking')}</span>
                </label>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={isRange ? handleSaveRange : handleSaveDay}
                  disabled={saving}
                  className="btn btn-secondary"
                >
                  {saving ? t('profile.saving') : t('partner.save')}
                </button>
                <button type="button" onClick={clearSelection} className="btn btn-tertiary">
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          )}

          {blocks.length > 0 && (
            <div className="partner-calendar-blocks">
              <h3 className="partner-calendar-blocks-title">{t('partner.externalBookingBlocks')}</h3>
              <ul className="partner-calendar-blocks-list">
                {blocks.map((block) => (
                  <li key={block.id} className="partner-calendar-block-item">
                    <span className="partner-calendar-block-dates">
                      {formatDay(block.date_from)} - {formatDay(addDays(block.date_to, -1))}
                    </span>
                    <span className="partner-calendar-block-rooms">{t('partner.blockRooms', { count: block.rooms })}</span>
                    <span className="partner-calendar-block-note">{block.note}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveBlock(block)}
                      className="btn btn-danger btn-sm"
                      aria-label={t('partner.removeBlockFor', { note: block.note, name: roomTypeName })}
                    >
                      {t('booking.remove')}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {blockModalOpen && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="block-modal-title">
          <div className="modal-content" ref={dialogRef} tabIndex={-1}>
            <h2 id="block-modal-title" className="modal-title">{t('partner.externalBooking')}</h2>
            <p className="modal-subtitle">{t('partner.takeRoomsOut', { name: roomTypeName })}</p>

            {blockError && (
              <div className="alert alert-error" role="alert" aria-live="polite">{blockError}</div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="block-date-from">{t('partner.from')}</label>
                <input
                  id="block-date-from"
                  type="date"
                  value={blockDateFrom}
                  onChange={(e) => setBlockDateFrom(e.target.value)}
                  className="form-input"
                  required
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="block-date-to">{t('partner.toExclusive')}</label>
                <input
                  id="block-date-to"
                  type="date"
                  value={blockDateTo}
                  onChange={(e) => setBlockDateTo(e.target.value)}
                  className="form-input"
                  required
                  aria-required="true"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="block-rooms">{t('partner.rooms')}</label>
              <input
                id="block-rooms"
                type="number"
                min={1}
                max={totalRooms}
                value={blockRooms}
                onChange={(e) => setBlockRooms(parseInt(e.target.value) || 1)}
                className="form-input"
                required
                aria-required="true"
              />
            </div>

            <div className="form-group">
              <label htmlFor="block-note">{t('partner.note')}</label>
              <input
                id="block-note"
                type="text"
                value={blockNote}
                onChange={(e) => setBlockNote(e.target.value)}
                className="form-input"
                placeholder={t('partner.notePlaceholder')}
                required
                aria-required="true"
              />
            </div>

            <div className="modal-actions">
              <button
                type="button"
                onClick={handleCreateBlock}
                disabled={blockSaving || !blockNote.trim()}
                className="btn btn-primary"
              >
                {blockSaving ? t('partner.creating') : t('partner.createBlock')}
              </button>
              <button type="button" onClick={closeBlockModal} disabled={blockSaving} className="btn btn-secondary">
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
