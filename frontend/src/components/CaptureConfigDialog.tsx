import { useState, useEffect } from "react"
import { getApiUrl } from "@/config/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Database, Calendar, Hash, Star, Filter, Info } from "lucide-react"
import { FilterKeywordsManager } from "./FilterKeywordsManager"

export interface CaptureConfigValues {
  days_back?: number
  max_results?: number
  target_date?: string
  date_from?: string
  date_to?: string
  min_relevance?: number
}

interface CaptureConfigDialogProps {
  open: boolean
  source: "BDNS" | "BOE"
  onCapture: (config: CaptureConfigValues) => void
  onCancel: () => void
  isCapturing: boolean
}

export function CaptureConfigDialog({
  open,
  source,
  onCapture,
  onCancel,
  isCapturing,
}: CaptureConfigDialogProps) {
  // Get today's date in YYYY-MM-DD format
  const getTodayString = () => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }

  const [config, setConfig] = useState<CaptureConfigValues>(
    source === "BDNS"
      ? { date_from: getTodayString(), date_to: getTodayString(), max_results: 50 }
      : { target_date: "", min_relevance: 0.3 }
  )
  const [showFiltersManager, setShowFiltersManager] = useState(false)
  const [filtersSummary, setFiltersSummary] = useState<any>(null)

  // Load filters summary when dialog opens
  useEffect(() => {
    if (open) {
      fetch(getApiUrl("/api/v1/filters/summary"))
        .then(res => res.json())
        .then(data => setFiltersSummary(data))
        .catch(err => console.error("Error loading filters summary:", err))
    }
  }, [open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCapture(config)
  }

  const isBDNS = source === "BDNS"
  const currentFilters = isBDNS ? filtersSummary?.bdns : filtersSummary?.boe

  return (
    <Dialog open={open} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Configuración de Captura {source}
          </DialogTitle>
          <DialogDescription>
            {isBDNS
              ? "Configura los parámetros para la captura de grants desde la Base de Datos Nacional de Subvenciones (BDNS)."
              : "Configura los parámetros para la captura de grants desde el Boletín Oficial del Estado (BOE)."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {isBDNS ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="date_from" className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Fecha desde
                  </Label>
                  <Input
                    id="date_from"
                    type="date"
                    value={config.date_from || getTodayString()}
                    onChange={(e) =>
                      setConfig({ ...config, date_from: e.target.value })
                    }
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    Fecha de inicio para la búsqueda (por defecto: hoy)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="date_to" className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Fecha hasta
                  </Label>
                  <Input
                    id="date_to"
                    type="date"
                    value={config.date_to || getTodayString()}
                    onChange={(e) =>
                      setConfig({ ...config, date_to: e.target.value })
                    }
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    Fecha final para la búsqueda (por defecto: hoy)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_results" className="flex items-center gap-2">
                    <Hash className="h-4 w-4" />
                    Máximo de resultados
                  </Label>
                  <Input
                    id="max_results"
                    type="number"
                    min="1"
                    max="100"
                    step="1"
                    value={config.max_results || 50}
                    onChange={(e) =>
                      setConfig({ ...config, max_results: parseInt(e.target.value) })
                    }
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    Número máximo de grants a capturar (1-100)
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="target_date" className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Fecha objetivo
                  </Label>
                  <Input
                    id="target_date"
                    type="date"
                    value={config.target_date || ""}
                    onChange={(e) =>
                      setConfig({ ...config, target_date: e.target.value })
                    }
                  />
                  <p className="text-sm text-muted-foreground">
                    Fecha del BOE a procesar (vacío = hoy)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="min_relevance" className="flex items-center gap-2">
                    <Star className="h-4 w-4" />
                    Relevancia mínima (%)
                  </Label>
                  <Input
                    id="min_relevance"
                    type="number"
                    min="0"
                    max="100"
                    step="10"
                    value={((config.min_relevance || 0.3) * 100).toFixed(0)}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        min_relevance: parseFloat(e.target.value) / 100,
                      })
                    }
                    required
                  />
                  <p className="text-sm text-muted-foreground">
                    Solo grants con relevancia mayor o igual (0-100%)
                  </p>
                </div>
              </>
            )}

            {/* Filters Summary */}
            {currentFilters && (
              <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <span className="font-semibold text-sm">Filtros Activos</span>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFiltersManager(true)}
                  >
                    Ver/Editar
                  </Button>
                </div>

                <div className="space-y-2 text-sm">
                  {isBDNS ? (
                    <>
                      <div className="flex items-start gap-2">
                        <Info className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                        <div>
                          <span className="font-medium">{currentFilters.total_keywords} keywords</span>
                          <span className="text-muted-foreground"> nonprofit (ej: </span>
                          {currentFilters.sample_keywords?.slice(0, 3).map((kw: string, i: number) => (
                            <Badge key={i} variant="secondary" className="mx-1 text-xs">
                              {kw}
                            </Badge>
                          ))}
                          <span className="text-muted-foreground">...)</span>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground pl-6">
                        Modo: {currentFilters.filter_mode}
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-start gap-2">
                        <Info className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                        <div>
                          <span className="font-medium">{currentFilters.total_grant_keywords} keywords</span>
                          <span className="text-muted-foreground"> de grants (ej: </span>
                          {currentFilters.sample_keywords?.slice(0, 3).map((kw: string, i: number) => (
                            <Badge key={i} variant="secondary" className="mx-1 text-xs">
                              {kw}
                            </Badge>
                          ))}
                          <span className="text-muted-foreground">...)</span>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground pl-6">
                        {currentFilters.total_sections} secciones BOE escaneadas
                      </div>
                      <div className="text-xs text-muted-foreground pl-6">
                        Relevancia: {currentFilters.relevance_filtering}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                ℹ️{" "}
                <strong>
                  {isBDNS
                    ? "Solo se capturarán grants identificados como nonprofit con alta confianza."
                    : "El score de relevancia es informativo y NO excluye ningún grant."}
                </strong>
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isCapturing}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isCapturing}>
              {isCapturing ? "⏳ Capturando..." : "📥 Iniciar Captura"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>

      {/* Filter Keywords Manager Dialog */}
      <FilterKeywordsManager
        open={showFiltersManager}
        onClose={() => {
          setShowFiltersManager(false)
          // Reload filters summary after editing
          fetch(getApiUrl("/api/v1/filters/summary"))
            .then(res => res.json())
            .then(data => setFiltersSummary(data))
            .catch(err => console.error("Error reloading filters:", err))
        }}
      />
    </Dialog>
  )
}
