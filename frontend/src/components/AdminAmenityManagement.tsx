import { useState, useEffect } from 'react'
import { SegmentedControl } from './SegmentedControl'
import { 
  adminAdapter, 
  AdminAmenity, 
  AdminAmenityCategory,
  CreateAmenityRequest,
  UpdateAmenityRequest,
  CreateAmenityCategoryRequest,
  UpdateAmenityCategoryRequest
} from '../adapters/adminAdapter'

type ViewMode = 'amenities' | 'categories'
type FormMode = 'create' | 'edit' | null

export function AdminAmenityManagement() {
  const [viewMode, setViewMode] = useState<ViewMode>('amenities')
  const [amenities, setAmenities] = useState<AdminAmenity[]>([])
  const [categories, setCategories] = useState<AdminAmenityCategory[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<FormMode>(null)
  const [selectedItem, setSelectedItem] = useState<AdminAmenity | AdminAmenityCategory | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  // Form state for amenities
  const [amenityForm, setAmenityForm] = useState<CreateAmenityRequest>({
    category: 0,
    name: '',
    slug: '',
    description: '',
    icon: '',
    is_searchable: true,
    sort_order: 0,
  })

  // Form state for categories
  const [categoryForm, setCategoryForm] = useState<CreateAmenityCategoryRequest>({
    name: '',
    slug: '',
    description: '',
    icon: '',
    sort_order: 0,
  })

  useEffect(() => {
    loadData()
  }, [viewMode])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      if (viewMode === 'amenities') {
        const response = await adminAdapter.getAmenities()
        if (response.error) {
          setError(response.error)
        } else if (response.data) {
          const sortedAmenities = [...response.data].sort((a, b) => a.sort_order - b.sort_order)
          setAmenities(sortedAmenities)
        }
      } else {
        const response = await adminAdapter.getAmenityCategories()
        if (response.error) {
          setError(response.error)
        } else if (response.data) {
          const sortedCategories = [...response.data].sort((a, b) => a.sort_order - b.sort_order)
          setCategories(sortedCategories)
        }
      }
    } catch (err) {
      setError('Failed to load data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAmenity = async () => {
    setActionLoading(null)
    setError(null)

    try {
      const response = await adminAdapter.createAmenity(amenityForm)
      
      if (response.error) {
        setError(response.error)
      } else {
        setFormMode(null)
        resetAmenityForm()
        await loadData()
      }
    } catch (err) {
      setError('Failed to create amenity. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleUpdateAmenity = async () => {
    if (!selectedItem || 'category_name' in selectedItem) return

    setActionLoading(selectedItem.id)
    setError(null)

    try {
      const updateData: UpdateAmenityRequest = {
        name: amenityForm.name || undefined,
        slug: amenityForm.slug || undefined,
        description: amenityForm.description || undefined,
        icon: amenityForm.icon || undefined,
        is_searchable: amenityForm.is_searchable,
        sort_order: amenityForm.sort_order,
      }

      const response = await adminAdapter.updateAmenity(selectedItem.id, updateData)
      
      if (response.error) {
        setError(response.error)
      } else {
        setFormMode(null)
        setSelectedItem(null)
        resetAmenityForm()
        await loadData()
      }
    } catch (err) {
      setError('Failed to update amenity. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeleteAmenity = async (id: number) => {
    if (!confirm('Are you sure you want to delete this amenity?')) return

    setActionLoading(id)
    setError(null)

    try {
      const response = await adminAdapter.deleteAmenity(id)
      
      if (response.error) {
        setError(response.error)
      } else {
        await loadData()
      }
    } catch (err) {
      setError('Failed to delete amenity. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCreateCategory = async () => {
    setActionLoading(null)
    setError(null)

    try {
      const response = await adminAdapter.createAmenityCategory(categoryForm)
      
      if (response.error) {
        setError(response.error)
      } else {
        setFormMode(null)
        resetCategoryForm()
        await loadData()
      }
    } catch (err) {
      setError('Failed to create category. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleUpdateCategory = async () => {
    if (!selectedItem || !('category_name' in selectedItem)) return

    setActionLoading(selectedItem.id)
    setError(null)

    try {
      const updateData: UpdateAmenityCategoryRequest = {
        name: categoryForm.name || undefined,
        slug: categoryForm.slug || undefined,
        description: categoryForm.description || undefined,
        icon: categoryForm.icon || undefined,
        sort_order: categoryForm.sort_order,
      }

      const response = await adminAdapter.updateAmenityCategory(selectedItem.id, updateData)
      
      if (response.error) {
        setError(response.error)
      } else {
        setFormMode(null)
        setSelectedItem(null)
        resetCategoryForm()
        await loadData()
      }
    } catch (err) {
      setError('Failed to update category. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeleteCategory = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category? This will affect all amenities in this category.')) return

    setActionLoading(id)
    setError(null)

    try {
      const response = await adminAdapter.deleteAmenityCategory(id)
      
      if (response.error) {
        setError(response.error)
      } else {
        await loadData()
      }
    } catch (err) {
      setError('Failed to delete category. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  const resetAmenityForm = () => {
    setAmenityForm({
      category: 0,
      name: '',
      slug: '',
      description: '',
      icon: '',
      is_searchable: true,
      sort_order: 0,
    })
  }

  const resetCategoryForm = () => {
    setCategoryForm({
      name: '',
      slug: '',
      description: '',
      icon: '',
      sort_order: 0,
    })
  }

  const openCreateForm = () => {
    setFormMode('create')
    setSelectedItem(null)
    if (viewMode === 'amenities') {
      resetAmenityForm()
    } else {
      resetCategoryForm()
    }
  }

  const openEditForm = (item: AdminAmenity | AdminAmenityCategory) => {
    setFormMode('edit')
    setSelectedItem(item)
    if (viewMode === 'amenities' && !('category_name' in item)) {
      const amenity = item as AdminAmenity
      setAmenityForm({
        category: amenity.category,
        name: amenity.name,
        slug: amenity.slug,
        description: amenity.description,
        icon: amenity.icon,
        is_searchable: amenity.is_searchable,
        sort_order: amenity.sort_order,
      })
    } else if ('category_name' in item) {
      const category = item as AdminAmenityCategory
      setCategoryForm({
        name: category.name,
        slug: category.slug,
        description: category.description,
        icon: category.icon,
        sort_order: category.sort_order,
      })
    }
  }

  const closeForm = () => {
    setFormMode(null)
    setSelectedItem(null)
    resetAmenityForm()
    resetCategoryForm()
  }

  return (
    <div className="admin-amenity-management">
      <div className="admin-view-header">
        <h1 className="admin-view-title">Amenity Management</h1>
        <p className="admin-view-subtitle">Manage amenity categories and amenities</p>
      </div>

      <SegmentedControl<ViewMode>
        mode="tabs"
        aria-label="Amenity views"
        value={viewMode}
        onChange={setViewMode}
        options={[
          { value: 'amenities', label: 'Amenities' },
          { value: 'categories', label: 'Categories' },
        ]}
      />

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {formMode && (
        <div className="form-panel">
          <h2 className="form-panel-title">
            {formMode === 'create' ? `Create ${viewMode === 'amenities' ? 'Amenity' : 'Category'}` : `Edit ${viewMode === 'amenities' ? 'Amenity' : 'Category'}`}
          </h2>
          
          {viewMode === 'amenities' ? (
            <div className="form-fields">
              <div className="form-group">
                <label htmlFor="amenity-category">Category:</label>
                <select
                  id="amenity-category"
                  value={amenityForm.category}
                  onChange={(e) => setAmenityForm({ ...amenityForm, category: parseInt(e.target.value) })}
                  className="form-control"
                  required
                >
                  <option value={0}>Select a category</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="amenity-name">Name:</label>
                <input
                  id="amenity-name"
                  type="text"
                  value={amenityForm.name}
                  onChange={(e) => setAmenityForm({ ...amenityForm, name: e.target.value })}
                  className="form-control"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="amenity-slug">Slug:</label>
                <input
                  id="amenity-slug"
                  type="text"
                  value={amenityForm.slug}
                  onChange={(e) => setAmenityForm({ ...amenityForm, slug: e.target.value })}
                  className="form-control"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="amenity-description">Description:</label>
                <textarea
                  id="amenity-description"
                  value={amenityForm.description}
                  onChange={(e) => setAmenityForm({ ...amenityForm, description: e.target.value })}
                  className="form-control"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label htmlFor="amenity-icon">Icon:</label>
                <input
                  id="amenity-icon"
                  type="text"
                  value={amenityForm.icon}
                  onChange={(e) => setAmenityForm({ ...amenityForm, icon: e.target.value })}
                  className="form-control"
                  placeholder="e.g., wifi, parking, pool"
                />
              </div>
              <div className="form-group">
                <label htmlFor="amenity-sort-order">Sort Order:</label>
                <input
                  id="amenity-sort-order"
                  type="number"
                  value={amenityForm.sort_order}
                  onChange={(e) => setAmenityForm({ ...amenityForm, sort_order: parseInt(e.target.value) })}
                  className="form-control"
                />
              </div>
              <div className="form-group checkbox-group">
                <input
                  id="amenity-searchable"
                  type="checkbox"
                  checked={amenityForm.is_searchable}
                  onChange={(e) => setAmenityForm({ ...amenityForm, is_searchable: e.target.checked })}
                />
                <label htmlFor="amenity-searchable">Searchable in filters</label>
              </div>
              <div className="form-actions">
                <button
                  onClick={formMode === 'create' ? handleCreateAmenity : handleUpdateAmenity}
                  disabled={actionLoading !== null}
                  className="btn btn-primary"
                >
                  {actionLoading !== null ? 'Processing...' : (formMode === 'create' ? 'Create' : 'Update')}
                </button>
                <button
                  onClick={closeForm}
                  disabled={actionLoading !== null}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="form-fields">
              <div className="form-group">
                <label htmlFor="category-name">Name:</label>
                <input
                  id="category-name"
                  type="text"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  className="form-control"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="category-slug">Slug:</label>
                <input
                  id="category-slug"
                  type="text"
                  value={categoryForm.slug}
                  onChange={(e) => setCategoryForm({ ...categoryForm, slug: e.target.value })}
                  className="form-control"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="category-description">Description:</label>
                <textarea
                  id="category-description"
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                  className="form-control"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label htmlFor="category-icon">Icon:</label>
                <input
                  id="category-icon"
                  type="text"
                  value={categoryForm.icon}
                  onChange={(e) => setCategoryForm({ ...categoryForm, icon: e.target.value })}
                  className="form-control"
                  placeholder="e.g., kitchen, bathroom, entertainment"
                />
              </div>
              <div className="form-group">
                <label htmlFor="category-sort-order">Sort Order:</label>
                <input
                  id="category-sort-order"
                  type="number"
                  value={categoryForm.sort_order}
                  onChange={(e) => setCategoryForm({ ...categoryForm, sort_order: parseInt(e.target.value) })}
                  className="form-control"
                />
              </div>
              <div className="form-actions">
                <button
                  onClick={formMode === 'create' ? handleCreateCategory : handleUpdateCategory}
                  disabled={actionLoading !== null}
                  className="btn btn-primary"
                >
                  {actionLoading !== null ? 'Processing...' : (formMode === 'create' ? 'Create' : 'Update')}
                </button>
                <button
                  onClick={closeForm}
                  disabled={actionLoading !== null}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading {viewMode === 'amenities' ? 'amenities' : 'categories'}...
        </div>
      ) : viewMode === 'amenities' && amenities.length === 0 ? (
        <div className="empty-state">
          <p>No amenities found.</p>
          <button onClick={openCreateForm} className="btn btn-primary">
            Create First Amenity
          </button>
        </div>
      ) : viewMode === 'categories' && categories.length === 0 ? (
        <div className="empty-state">
          <p>No categories found.</p>
          <button onClick={openCreateForm} className="btn btn-primary">
            Create First Category
          </button>
        </div>
      ) : (
        <div className="items-list">
          <div className="list-header">
            <button onClick={openCreateForm} className="btn btn-primary">
              Create {viewMode === 'amenities' ? 'Amenity' : 'Category'}
            </button>
          </div>
          
          {viewMode === 'amenities' ? (
            amenities.map(amenity => (
              <div key={amenity.id} className="item-card">
                <div className="item-card-header">
                  <div className="item-info">
                    <h3 className="item-name">{amenity.name}</h3>
                    <p className="item-slug">{amenity.slug}</p>
                    <p className="item-category">Category: {amenity.category_name || `ID: ${amenity.category}`}</p>
                  </div>
                  <div className="item-badges">
                    {amenity.is_searchable && <span className="badge badge-success">Searchable</span>}
                  </div>
                </div>
                <div className="item-card-body">
                  <p className="item-description">{amenity.description}</p>
                  <div className="item-details">
                    <span className="detail-label">Icon:</span>
                    <span className="detail-value">{amenity.icon || 'None'}</span>
                    <span className="detail-label">Sort Order:</span>
                    <span className="detail-value">{amenity.sort_order}</span>
                  </div>
                </div>
                <div className="item-card-footer">
                  <div className="item-actions">
                    <button
                      onClick={() => openEditForm(amenity)}
                      disabled={actionLoading === amenity.id}
                      className="btn btn-secondary"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteAmenity(amenity.id)}
                      disabled={actionLoading === amenity.id}
                      className="btn btn-danger"
                    >
                      {actionLoading === amenity.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            categories.map(category => (
              <div key={category.id} className="item-card">
                <div className="item-card-header">
                  <div className="item-info">
                    <h3 className="item-name">{category.name}</h3>
                    <p className="item-slug">{category.slug}</p>
                  </div>
                </div>
                <div className="item-card-body">
                  <p className="item-description">{category.description}</p>
                  <div className="item-details">
                    <span className="detail-label">Icon:</span>
                    <span className="detail-value">{category.icon || 'None'}</span>
                    <span className="detail-label">Sort Order:</span>
                    <span className="detail-value">{category.sort_order}</span>
                  </div>
                </div>
                <div className="item-card-footer">
                  <div className="item-actions">
                    <button
                      onClick={() => openEditForm(category)}
                      disabled={actionLoading === category.id}
                      className="btn btn-secondary"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteCategory(category.id)}
                      disabled={actionLoading === category.id}
                      className="btn btn-danger"
                    >
                      {actionLoading === category.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
