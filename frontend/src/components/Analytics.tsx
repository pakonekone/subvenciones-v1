import { useState, useEffect } from 'react'
import { getApiUrl } from "@/config/api"

interface AnalyticsData {
  total_grants: number
  total_budget: number
  nonprofit_grants: number
  open_grants: number
  sent_to_n8n: number
  avg_confidence: number
  grants_by_source: {
    source: string
    count: number
    total_budget: number
    nonprofit_count: number
    open_count: number
    sent_to_n8n_count: number
  }[]
  grants_by_date: {
    date: string
    count: number
    total_budget: number
  }[]
  budget_distribution: {
    range: string
    count: number
    total_budget: number
  }[]
  top_departments: {
    department: string
    count: number
    total_budget: number
    avg_budget: number
  }[]
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)

  const API_BASE = '/api/v1'

  useEffect(() => {
    loadAnalytics()
  }, [days])

  const loadAnalytics = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/analytics/overview?days=${days}`)
      if (!response.ok) throw new Error('Error cargando analytics')
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('es-ES').format(num)
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">⏳ Cargando analytics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">⚠️ {error}</div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="container">
      <div className="header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Estadísticas y tendencias de grants capturados</p>
      </div>

      {/* Period Selector */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>Período:</span>
        <button
          className={`btn ${days === 7 ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setDays(7)}
        >
          7 días
        </button>
        <button
          className={`btn ${days === 30 ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setDays(30)}
        >
          30 días
        </button>
        <button
          className={`btn ${days === 90 ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setDays(90)}
        >
          90 días
        </button>
        <button
          className={`btn ${days === 365 ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setDays(365)}
        >
          1 año
        </button>
      </div>

      {/* Key Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Total Grants</div>
          <div style={{ fontSize: '32px', fontWeight: 700 }}>{formatNumber(data.total_grants)}</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Presupuesto Total</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{formatAmount(data.total_budget)}</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Nonprofit</div>
          <div style={{ fontSize: '32px', fontWeight: 700 }}>
            {formatNumber(data.nonprofit_grants)}
            <span style={{ fontSize: '16px', opacity: 0.8, marginLeft: '8px' }}>
              ({((data.nonprofit_grants / data.total_grants) * 100).toFixed(1)}%)
            </span>
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Abiertas</div>
          <div style={{ fontSize: '32px', fontWeight: 700 }}>{formatNumber(data.open_grants)}</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Enviadas N8n</div>
          <div style={{ fontSize: '32px', fontWeight: 700 }}>{formatNumber(data.sent_to_n8n)}</div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
          padding: '20px',
          borderRadius: '12px',
          color: 'white'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px' }}>Confianza Media</div>
          <div style={{ fontSize: '32px', fontWeight: 700 }}>
            {(data.avg_confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* By Source */}
        <div className="table-container">
          <h2 style={{ marginBottom: '16px' }}>📦 Por Fuente</h2>
          {data.grants_by_source.map(source => (
            <div key={source.source} style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600 }}>{source.source}</span>
                <span>{formatNumber(source.count)} grants</span>
              </div>
              <div style={{
                background: '#e3f2fd',
                borderRadius: '8px',
                height: '8px',
                overflow: 'hidden'
              }}>
                <div style={{
                  background: source.source === 'BDNS' ? '#2196f3' : '#ff9800',
                  height: '100%',
                  width: `${(source.count / data.total_grants) * 100}%`,
                  transition: 'width 0.3s'
                }}></div>
              </div>
              <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px' }}>
                {formatAmount(source.total_budget)} • {source.nonprofit_count} nonprofit •{' '}
                {source.open_count} abiertas • {source.sent_to_n8n_count} enviadas
              </div>
            </div>
          ))}
        </div>

        {/* Budget Distribution */}
        <div className="table-container">
          <h2 style={{ marginBottom: '16px' }}>💰 Distribución Presupuesto</h2>
          {data.budget_distribution.map(range => {
            const maxCount = Math.max(...data.budget_distribution.map(r => r.count))
            return (
              <div key={range.range} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600 }}>{range.range}</span>
                  <span>{formatNumber(range.count)} grants</span>
                </div>
                <div style={{
                  background: '#e8f5e9',
                  borderRadius: '8px',
                  height: '8px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: '#4caf50',
                    height: '100%',
                    width: `${(range.count / maxCount) * 100}%`,
                    transition: 'width 0.3s'
                  }}></div>
                </div>
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px' }}>
                  Total: {formatAmount(range.total_budget)}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Top Departments */}
      <div className="table-container">
        <h2 style={{ marginBottom: '16px' }}>🏢 Top 10 Departamentos</h2>
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Departamento</th>
              <th>Grants</th>
              <th>Presupuesto Total</th>
              <th>Presupuesto Medio</th>
            </tr>
          </thead>
          <tbody>
            {data.top_departments.map((dept, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 600 }}>{dept.department}</td>
                <td style={{ textAlign: 'center' }}>
                  <span className="badge badge-info">{formatNumber(dept.count)}</span>
                </td>
                <td className="amount">{formatAmount(dept.total_budget)}</td>
                <td className="amount">{formatAmount(dept.avg_budget)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Timeline Chart */}
      <div className="table-container" style={{ marginTop: '32px' }}>
        <h2 style={{ marginBottom: '16px' }}>📈 Grants por Día</h2>
        <div style={{ height: '300px', display: 'flex', alignItems: 'flex-end', gap: '4px' }}>
          {data.grants_by_date.slice(-30).map((point, idx) => {
            const maxCount = Math.max(...data.grants_by_date.map(p => p.count))
            const height = (point.count / maxCount) * 100
            return (
              <div
                key={idx}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-end',
                  alignItems: 'center'
                }}
              >
                <div
                  style={{
                    background: 'linear-gradient(180deg, #667eea 0%, #764ba2 100%)',
                    width: '100%',
                    height: `${height}%`,
                    borderRadius: '4px 4px 0 0',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'opacity 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '0.8'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '1'
                  }}
                  title={`${point.date}: ${point.count} grants, ${formatAmount(point.total_budget)}`}
                ></div>
              </div>
            )
          })}
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '8px',
          fontSize: '12px',
          color: '#7f8c8d'
        }}>
          <span>{data.grants_by_date[0]?.date || '-'}</span>
          <span>{data.grants_by_date[data.grants_by_date.length - 1]?.date || '-'}</span>
        </div>
      </div>
    </div>
  )
}
