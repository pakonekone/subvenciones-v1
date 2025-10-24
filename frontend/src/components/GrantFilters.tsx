import { useState } from 'react'

export interface FilterValues {
  search: string
  department: string
  dateFrom: string
  dateTo: string
  budgetMin: string
  budgetMax: string
  confidenceMin: string
  isOpen: string
  sentToN8n: string
}

interface GrantFiltersProps {
  onFilterChange: (filters: FilterValues) => void
  onClear: () => void
}

export default function GrantFilters({ onFilterChange, onClear }: GrantFiltersProps) {
  const [filters, setFilters] = useState<FilterValues>({
    search: '',
    department: '',
    dateFrom: '',
    dateTo: '',
    budgetMin: '',
    budgetMax: '',
    confidenceMin: '',
    isOpen: 'all',
    sentToN8n: 'all'
  })

  const [showFilters, setShowFilters] = useState(false)

  const handleChange = (field: keyof FilterValues, value: string) => {
    const newFilters = { ...filters, [field]: value }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleClear = () => {
    const emptyFilters: FilterValues = {
      search: '',
      department: '',
      dateFrom: '',
      dateTo: '',
      budgetMin: '',
      budgetMax: '',
      confidenceMin: '',
      isOpen: 'all',
      sentToN8n: 'all'
    }
    setFilters(emptyFilters)
    onClear()
  }

  const hasActiveFilters = () => {
    return filters.search || filters.department || filters.dateFrom || filters.dateTo ||
           filters.budgetMin || filters.budgetMax || filters.confidenceMin ||
           filters.isOpen !== 'all' || filters.sentToN8n !== 'all'
  }

  return (
    <div className="filters-container">
      <div className="filters-header">
        <button
          className="btn btn-secondary"
          onClick={() => setShowFilters(!showFilters)}
        >
          🔍 {showFilters ? 'Ocultar' : 'Mostrar'} Filtros
          {hasActiveFilters() && <span className="filter-badge">{' • Activos'}</span>}
        </button>

        {hasActiveFilters() && (
          <button className="btn btn-secondary" onClick={handleClear}>
            ❌ Limpiar Filtros
          </button>
        )}
      </div>

      {showFilters && (
        <div className="filters-content">
          <div className="filter-grid">
            {/* Búsqueda de texto */}
            <div className="filter-item">
              <label>🔍 Búsqueda</label>
              <input
                type="text"
                placeholder="Buscar en título o finalidad..."
                value={filters.search}
                onChange={(e) => handleChange('search', e.target.value)}
                className="filter-input"
              />
            </div>

            {/* Organismo */}
            <div className="filter-item">
              <label>🏢 Organismo</label>
              <input
                type="text"
                placeholder="Ej: Diputación, Ministerio..."
                value={filters.department}
                onChange={(e) => handleChange('department', e.target.value)}
                className="filter-input"
              />
            </div>

            {/* Fecha Desde */}
            <div className="filter-item">
              <label>📅 Fecha Límite Desde</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => handleChange('dateFrom', e.target.value)}
                className="filter-input"
              />
            </div>

            {/* Fecha Hasta */}
            <div className="filter-item">
              <label>📅 Fecha Límite Hasta</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => handleChange('dateTo', e.target.value)}
                className="filter-input"
              />
            </div>

            {/* Presupuesto Mínimo */}
            <div className="filter-item">
              <label>💰 Presupuesto Mínimo (€)</label>
              <input
                type="number"
                placeholder="0"
                value={filters.budgetMin}
                onChange={(e) => handleChange('budgetMin', e.target.value)}
                className="filter-input"
                min="0"
                step="1000"
              />
            </div>

            {/* Presupuesto Máximo */}
            <div className="filter-item">
              <label>💰 Presupuesto Máximo (€)</label>
              <input
                type="number"
                placeholder="1000000"
                value={filters.budgetMax}
                onChange={(e) => handleChange('budgetMax', e.target.value)}
                className="filter-input"
                min="0"
                step="1000"
              />
            </div>

            {/* Confianza Mínima */}
            <div className="filter-item">
              <label>🎯 Confianza Nonprofit Mín (%)</label>
              <input
                type="number"
                placeholder="0"
                value={filters.confidenceMin}
                onChange={(e) => handleChange('confidenceMin', e.target.value)}
                className="filter-input"
                min="0"
                max="100"
                step="10"
              />
            </div>

            {/* Estado */}
            <div className="filter-item">
              <label>🚦 Estado</label>
              <select
                value={filters.isOpen}
                onChange={(e) => handleChange('isOpen', e.target.value)}
                className="filter-input"
              >
                <option value="all">Todas</option>
                <option value="true">Abiertas</option>
                <option value="false">Cerradas</option>
              </select>
            </div>

            {/* Enviado a N8n */}
            <div className="filter-item">
              <label>📤 Enviado a N8n</label>
              <select
                value={filters.sentToN8n}
                onChange={(e) => handleChange('sentToN8n', e.target.value)}
                className="filter-input"
              >
                <option value="all">Todos</option>
                <option value="true">Enviados</option>
                <option value="false">Pendientes</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
