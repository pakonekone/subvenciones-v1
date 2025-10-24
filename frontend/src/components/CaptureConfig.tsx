import { useState } from 'react'

export interface CaptureConfigValues {
  days_back?: number
  max_results?: number
  target_date?: string
  min_relevance?: number
}

interface CaptureConfigProps {
  source: 'BDNS' | 'BOE'
  onCapture: (config: CaptureConfigValues) => void
  onCancel: () => void
  isCapturing: boolean
}

export default function CaptureConfig({ source, onCapture, onCancel, isCapturing }: CaptureConfigProps) {
  const [config, setConfig] = useState<CaptureConfigValues>(
    source === 'BDNS'
      ? { days_back: 7, max_results: 50 }
      : { target_date: '', min_relevance: 0.3 }
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCapture(config)
  }

  const isBDNS = source === 'BDNS'

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h2>⚙️ Configuración de Captura {source}</h2>
          <button className="modal-close" onClick={onCancel}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="config-section">
              <p style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '20px' }}>
                {isBDNS
                  ? 'Configura los parámetros para la captura de grants desde la Base de Datos Nacional de Subvenciones (BDNS).'
                  : 'Configura los parámetros para la captura de grants desde el Boletín Oficial del Estado (BOE).'}
              </p>

              {isBDNS ? (
                <>
                  <div className="detail-item" style={{ marginBottom: '20px' }}>
                    <label htmlFor="days_back" style={{ fontSize: '14px', fontWeight: 600, color: '#2c3e50' }}>
                      📅 Días hacia atrás
                    </label>
                    <input
                      id="days_back"
                      type="number"
                      min="1"
                      max="365"
                      value={config.days_back || 7}
                      onChange={(e) => setConfig({ ...config, days_back: parseInt(e.target.value) })}
                      className="filter-input"
                      required
                    />
                    <small style={{ fontSize: '12px', color: '#95a5a6' }}>
                      Número de días hacia atrás para buscar convocatorias (1-365)
                    </small>
                  </div>

                  <div className="detail-item" style={{ marginBottom: '20px' }}>
                    <label htmlFor="max_results" style={{ fontSize: '14px', fontWeight: 600, color: '#2c3e50' }}>
                      🔢 Máximo de resultados
                    </label>
                    <input
                      id="max_results"
                      type="number"
                      min="10"
                      max="500"
                      step="10"
                      value={config.max_results || 50}
                      onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) })}
                      className="filter-input"
                      required
                    />
                    <small style={{ fontSize: '12px', color: '#95a5a6' }}>
                      Número máximo de grants a capturar (10-500)
                    </small>
                  </div>
                </>
              ) : (
                <>
                  <div className="detail-item" style={{ marginBottom: '20px' }}>
                    <label htmlFor="target_date" style={{ fontSize: '14px', fontWeight: 600, color: '#2c3e50' }}>
                      📅 Fecha objetivo
                    </label>
                    <input
                      id="target_date"
                      type="date"
                      value={config.target_date || ''}
                      onChange={(e) => setConfig({ ...config, target_date: e.target.value })}
                      className="filter-input"
                    />
                    <small style={{ fontSize: '12px', color: '#95a5a6' }}>
                      Fecha del BOE a procesar (vacío = hoy)
                    </small>
                  </div>

                  <div className="detail-item" style={{ marginBottom: '20px' }}>
                    <label htmlFor="min_relevance" style={{ fontSize: '14px', fontWeight: 600, color: '#2c3e50' }}>
                      ⭐ Relevancia mínima (%)
                    </label>
                    <input
                      id="min_relevance"
                      type="number"
                      min="0"
                      max="100"
                      step="10"
                      value={((config.min_relevance || 0.3) * 100).toFixed(0)}
                      onChange={(e) => setConfig({ ...config, min_relevance: parseFloat(e.target.value) / 100 })}
                      className="filter-input"
                      required
                    />
                    <small style={{ fontSize: '12px', color: '#95a5a6' }}>
                      Solo grants con relevancia mayor o igual (0-100%)
                    </small>
                  </div>
                </>
              )}

              <div className="config-info" style={{
                background: '#e3f2fd',
                padding: '12px',
                borderRadius: '6px',
                marginTop: '20px'
              }}>
                <p style={{ fontSize: '13px', color: '#1976d2', margin: 0 }}>
                  ℹ️ <strong>Nota:</strong> {isBDNS
                    ? 'Solo se capturarán grants identificados como nonprofit con alta confianza.'
                    : 'El sistema identificará grants usando palabras clave y patrones del BOE.'}
                </p>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={isCapturing}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isCapturing}
            >
              {isCapturing ? '⏳ Capturando...' : '📥 Iniciar Captura'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
