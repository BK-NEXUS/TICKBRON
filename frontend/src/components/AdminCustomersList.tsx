import { ArrowDown, ArrowUp } from 'lucide-react'
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { adminAdapter, AdminCustomer, GetCustomersParams } from '../adapters/adminAdapter'
import { useI18n } from '../i18n/I18nContext'

const SORT_FIELDS = [
  { value: 'registration_date', labelKey: 'admin.registrationDate' },
  { value: 'full_name', labelKey: 'admin.name' },
  { value: 'email', labelKey: 'auth.email' },
  { value: 'total_booking_count', labelKey: 'admin.bookingCount' },
  { value: 'last_booking_date', labelKey: 'admin.lastBookingDate' },
  { value: 'total_amount_paid', labelKey: 'admin.totalPaid' },
  { value: 'customer_status', labelKey: 'status.statusCol' },
] as const

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const

export function AdminCustomersList() {
  const [customers, setCustomers] = useState<AdminCustomer[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('registration_date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  
  // Pagination metadata
  const [totalCount, setTotalCount] = useState(0)
  const [nextPage, setNextPage] = useState<string | null>(null)
  const [previousPage, setPreviousPage] = useState<string | null>(null)

  useEffect(() => {
    loadCustomers()
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, sortBy, sortOrder, currentPage, pageSize])

  const loadCustomers = async () => {
    setLoading(true)
    setError(null)

    const params: GetCustomersParams = {
      search: searchQuery || undefined,
      page: currentPage,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    }

    try {
      const response = await adminAdapter.getCustomers(params)
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setCustomers(response.data.results)
        setTotalCount(response.data.count)
        setNextPage(response.data.next)
        setPreviousPage(response.data.previous)
      }
    } catch (err) {
      setError(t('admin.failedToLoadCustomers'))
    } finally {
      setLoading(false)
    }
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    setCurrentPage(1) // Reset to first page on new search
  }

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSortBy(e.target.value)
  }

  const handleSortOrderToggle = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
  }

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value))
    setCurrentPage(1) // Reset to first page on page size change
  }

  const handlePreviousPage = () => {
    if (previousPage && currentPage > 1) {
      setCurrentPage(prev => prev - 1)
    }
  }

  const handleNextPage = () => {
    if (nextPage) {
      setCurrentPage(prev => prev + 1)
    }
  }

  const getStatusClass = (status: string) => {
    return status === 'active' ? 'status-badge--active' : 'status-badge--inactive'
  }

  const formatDate = (dateString: string) => (dateString ? formatLocalDate(dateString) : t('admin.na'))

  const { t, formatMoney, formatDate: formatLocalDate } = useI18n()

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return formatMoney(amount, currency)
  }

  const getContactMethodLabel = (method: string) => {
    const labels: Record<string, string> = {
      email: 'Email',
      phone: 'Phone',
      whatsapp: 'WhatsApp',
      telegram: 'Telegram',
    }
    return labels[method] || method
  }

  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="admin-customers-list">
      <div className="admin-view-header">
        <h1 className="admin-view-title">{t('admin.customersDirectory')}</h1>
        <p className="admin-view-subtitle">{t('admin.viewAndSearchCustomer')}</p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="customer-search" className="search-label">
            {t('admin.searchByNamePhone')}
          </label>
          <input
            id="customer-search"
            type="text"
            className="search-input"
            placeholder={t('admin.enterSearchTerm')}
            value={searchQuery}
            onChange={handleSearchChange}
            aria-label={t('admin.searchCustomers')}
          />
        </div>

        <div className="sort-controls">
          <div className="sort-field">
            <label htmlFor="sort-by" className="sort-label">
              {t('sort.label')}
            </label>
            <select
              id="sort-by"
              className="sort-select"
              value={sortBy}
              onChange={handleSortChange}
              aria-label={t('admin.sortCustomersBy')}
            >
              {SORT_FIELDS.map(field => (
                <option key={field.value} value={field.value}>
                  {t(field.labelKey)}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleSortOrderToggle}
            aria-label={t('admin.sortOrderLabel', { order: sortOrder === 'asc' ? t('status.ascending') : t('status.descending') })}
          >
            {sortOrder === 'asc' ? <ArrowUp size={14} aria-hidden="true" /> : <ArrowDown size={14} aria-hidden="true" />} {sortOrder === 'asc' ? t('admin.asc') : t('admin.desc')}
          </button>

          <div className="page-size-control">
            <label htmlFor="page-size" className="page-size-label">
              {t('admin.perPage')}
            </label>
            <select
              id="page-size"
              className="page-size-select"
              value={pageSize}
              onChange={handlePageSizeChange}
              aria-label={t('admin.itemsPerPage')}
            >
              {PAGE_SIZE_OPTIONS.map(size => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          {t('admin.loadingCustomers')}
        </div>
      ) : customers.length === 0 ? (
        <div className="empty-state">
          <p>{t('admin.noCustomersFound')}</p>
          <p>{t('admin.customersWillAppearHere')}</p>
        </div>
      ) : (
        <>
          {/* Customers Table */}
          <div className="customers-table-container">
            <div className="customers-count">
              <p>{t('admin.totalCustomers', { count: totalCount })}</p>
            </div>

            <table className="customers-table" role="table" aria-label={t('admin.customersDirectory2')}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.id')}</th>
                  <th scope="col">{t('admin.registrationDate')}</th>
                  <th scope="col">{t('admin.name')}</th>
                  <th scope="col">{t('profile.contact.phone')}</th>
                  <th scope="col">{t('auth.email')}</th>
                  <th scope="col">{t('profile.whatsapp')}</th>
                  <th scope="col">{t('profile.telegram')}</th>
                  <th scope="col">{t('admin.preferredContact')}</th>
                  <th scope="col">{t('admin.bookingCount')}</th>
                  <th scope="col">{t('admin.lastBookingDate')}</th>
                  <th scope="col">{t('admin.totalPaid')}</th>
                  <th scope="col">{t('partner.status')}</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(customer => (
                  <tr key={customer.id}>
                    <td className="customer-id">
                      <Link to={`/admin/customers/${customer.id}`} className="customer-link">
                        {customer.id}
                      </Link>
                    </td>
                    <td className="customer-registration-date">{formatDate(customer.registration_date)}</td>
                    <td className="customer-name">
                      <Link to={`/admin/customers/${customer.id}`} className="customer-link">
                        {customer.full_name}
                      </Link>
                    </td>
                    <td className="customer-phone">{customer.phone}</td>
                    <td className="customer-email">{customer.email}</td>
                    <td className="customer-whatsapp">{customer.whatsapp || 'N/A'}</td>
                    <td className="customer-telegram">{customer.telegram || 'N/A'}</td>
                    <td className="customer-preferred-contact">{getContactMethodLabel(customer.preferred_contact_method)}</td>
                    <td className="customer-booking-count">{customer.total_booking_count}</td>
                    <td className="customer-last-booking-date">{formatDate(customer.last_booking_date)}</td>
                    <td className="customer-total-paid">{formatCurrency(customer.total_amount_paid)}</td>
                    <td className="customer-status">
                      <span className={`status-badge ${getStatusClass(customer.customer_status)}`}>
                        {customer.customer_status === 'active' ? t('profile.active') : t('profile.inactive')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="pagination-controls" role="navigation" aria-label={t('status.pagination')}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handlePreviousPage}
              disabled={!previousPage || currentPage === 1}
              aria-label={t('admin.previousPage')}
            >
              {t('admin.previous')}
            </button>
            
            <div className="pagination-info">
              <span aria-live="polite">
                {t('admin.pageOf', { page: currentPage, total: totalPages })}
              </span>
            </div>
            
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleNextPage}
              disabled={!nextPage || currentPage === totalPages}
              aria-label={t('admin.nextPage')}
            >
              {t('partner.next')}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
