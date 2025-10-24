import { Grant } from '../types'

interface GrantDetailModalProps {
  grant: Grant | null
  onClose: () => void
}

export default function GrantDetailModal({ grant, onClose }: GrantDetailModalProps) {
  if (!grant) return null

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'No especificada'
    return new Date(dateStr).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatAmount = (amount: number | null) => {
    if (!amount) return 'No especificado'
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatList = (list: string[] | null) => {
    if (!list || list.length === 0) return 'No especificado'
    return list.join(', ')
  }

  const getConfidenceLabel = (confidence: number | null) => {
    if (!confidence) return 'No calculada'
    const percent = (confidence * 100).toFixed(0)
    if (confidence >= 0.7) return `🟢 Alta (${percent}%)`
    if (confidence >= 0.4) return `🟡 Media (${percent}%)`
    return `🔴 Baja (${percent}%)`
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{grant.title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Información Básica */}
          <section className="detail-section">
            <h3>📋 Información Básica</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Código:</strong>
                <span>{grant.bdns_code || grant.id}</span>
              </div>
              <div className="detail-item">
                <strong>Fuente:</strong>
                <span className="badge badge-info">{grant.source}</span>
              </div>
              <div className="detail-item">
                <strong>Organismo:</strong>
                <span>{grant.department || 'No especificado'}</span>
              </div>
              <div className="detail-item">
                <strong>Estado:</strong>
                <span>
                  {grant.is_open ? (
                    <span className="badge badge-success">
                      <span className="status-dot status-open"></span>
                      Abierta
                    </span>
                  ) : (
                    <span className="badge badge-warning">
                      <span className="status-dot status-closed"></span>
                      Cerrada
                    </span>
                  )}
                </span>
              </div>
            </div>
          </section>

          {/* Finalidad */}
          {grant.purpose && (
            <section className="detail-section">
              <h3>🎯 Finalidad</h3>
              <p className="detail-text">{grant.purpose}</p>
            </section>
          )}

          {/* Presupuesto y Fechas */}
          <section className="detail-section">
            <h3>💰 Presupuesto y Plazos</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Presupuesto Total:</strong>
                <span className="amount">{formatAmount(grant.budget_amount)}</span>
              </div>
              <div className="detail-item">
                <strong>Fecha Publicación:</strong>
                <span>{formatDate(grant.publication_date)}</span>
              </div>
              <div className="detail-item">
                <strong>Inicio Plazo:</strong>
                <span>{formatDate(grant.application_start_date)}</span>
              </div>
              <div className="detail-item">
                <strong>Fin Plazo:</strong>
                <span className="date" style={{ fontWeight: 600 }}>
                  {formatDate(grant.application_end_date)}
                </span>
              </div>
            </div>
          </section>

          {/* Beneficiarios y Alcance */}
          <section className="detail-section">
            <h3>👥 Beneficiarios y Alcance</h3>
            <div className="detail-grid">
              <div className="detail-item full-width">
                <strong>Tipos de Beneficiarios:</strong>
                <span>{formatList(grant.beneficiary_types)}</span>
              </div>
              <div className="detail-item full-width">
                <strong>Sectores:</strong>
                <span>{formatList(grant.sectors)}</span>
              </div>
              <div className="detail-item full-width">
                <strong>Regiones:</strong>
                <span>{formatList(grant.regions)}</span>
              </div>
            </div>
          </section>

          {/* Análisis Nonprofit */}
          <section className="detail-section">
            <h3>🎯 Análisis Nonprofit</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Confianza Nonprofit:</strong>
                <span>{getConfidenceLabel(grant.nonprofit_confidence)}</span>
              </div>
              <div className="detail-item">
                <strong>Nonprofit:</strong>
                <span>
                  {grant.is_nonprofit ? (
                    <span className="badge badge-success">Sí</span>
                  ) : (
                    <span className="badge badge-warning">No</span>
                  )}
                </span>
              </div>
            </div>
          </section>

          {/* Envío N8n */}
          <section className="detail-section">
            <h3>📤 Estado de Envío</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Enviado a N8n:</strong>
                <span>
                  {grant.sent_to_n8n ? (
                    <span className="badge badge-info">
                      <span className="status-dot status-sent"></span>
                      Enviado
                    </span>
                  ) : (
                    <span style={{ color: '#95a5a6' }}>Pendiente</span>
                  )}
                </span>
              </div>
            </div>
          </section>

          {/* Enlaces */}
          <section className="detail-section">
            <h3>🔗 Enlaces y Documentos</h3>
            <div className="detail-links">
              {grant.regulatory_base_url && (
                <a
                  href={grant.regulatory_base_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  📄 Bases Reguladoras
                </a>
              )}
              {grant.electronic_office && (
                <a
                  href={grant.electronic_office}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  🌐 Sede Electrónica
                </a>
              )}
              {grant.bdns_code && (
                <a
                  href={`https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/${grant.bdns_code}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  🔗 Ver en BDNS
                </a>
              )}
            </div>
          </section>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
