import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { adminAdapter, AdminCustomer, GetCustomersParams } from '../adapters/adminAdapter'
import { useI18n } from '../i18n/I18nContext'

const SORT_FIELDS = [
  { value: 'registration_date', label: 'Registration Date' },
  { value: 'full_name', label: 'Name' },
  { value: 'email', label: 'Email' },
  { value: 'total_booking_count', label: 'Booking Count' },
  { value: 'last_booking_date', label: 'Last Booking Date' },
  { value: 'total_amount_paid', label: 'Total Paid' },
  { value: 'customer_status', label: 'Status' },
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
      setError('Failed to load customers. Please try again.')
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

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const { formatMoney } = useI18n()

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
        <h1 className="admin-view-title">Customers Directory</h1>
        <p className="admin-view-subtitle">View and search customer information with booking history</p>
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
            Search by name, phone, email, or ID:
          </label>
          <input
            id="customer-search"
            type="text"
            className="search-input"
            placeholder="Enter search term..."
            value={searchQuery}
            onChange={handleSearchChange}
            aria-label="Search customers"
          />
        </div>

        <div className="sort-controls">
          <div className="sort-field">
            <label htmlFor="sort-by" className="sort-label">
              Sort by:
            </label>
            <select
              id="sort-by"
              className="sort-select"
              value={sortBy}
              onChange={handleSortChange}
              aria-label="Sort customers by"
            >
              {SORT_FIELDS.map(field => (
                <option key={field.value} value={field.value}>
                  {field.label}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleSortOrderToggle}
            aria-label={`Sort order: ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
          >
            {sortOrder === 'asc' ? '↑ Asc' : '↓ Desc'}
          </button>

          <div className="page-size-control">
            <label htmlFor="page-size" className="page-size-label">
              Per page:
            </label>
            <select
              id="page-size"
              className="page-size-select"
              value={pageSize}
              onChange={handlePageSizeChange}
              aria-label="Items per page"
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
          Loading customers...
        </div>
      ) : customers.length === 0 ? (
        <div className="empty-state">
          <p>No customers found.</p>
          <p>Customers will appear here once they register or make bookings.</p>
        </div>
      ) : (
        <>
          {/* Customers Table */}
          <div className="customers-table-container">
            <div className="customers-count">
              <p>Total customers: {totalCount}</p>
            </div>

            <table className="customers-table" role="table" aria-label="Customers directory">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Registration Date</th>
                  <th scope="col">Name</th>
                  <th scope="col">Phone</th>
                  <th scope="col">Email</th>
                  <th scope="col">WhatsApp</th>
                  <th scope="col">Telegram</th>
                  <th scope="col">Preferred Contact</th>
                  <th scope="col">Booking Count</th>
                  <th scope="col">Last Booking Date</th>
                  <th scope="col">Total Paid</th>
                  <th scope="col">Status</th>
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
                        {customer.customer_status === 'active' ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="pagination-controls" role="navigation" aria-label="Pagination">
            <button
              className="btn btn-secondary btn-sm"
              onClick={handlePreviousPage}
              disabled={!previousPage || currentPage === 1}
              aria-label="Previous page"
            >
              Previous
            </button>
            
            <div className="pagination-info">
              <span aria-live="polite">
                Page {currentPage} of {totalPages}
              </span>
            </div>
            
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleNextPage}
              disabled={!nextPage || currentPage === totalPages}
              aria-label="Next page"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
