import { useState, useEffect } from "react"
import { Grant, GrantsResponse } from "@/types"
import { QuickFilters, QuickFilter } from "@/components/QuickFilters"
import {
  AdvancedFilterPanel,
  AdvancedFilters,
  DEFAULT_FILTERS,
} from "@/components/AdvancedFilterPanel"
import { GrantsTable } from "@/components/GrantsTable"
import { ConvocatoriaGrid } from "@/components/ConvocatoriaCard"
import { GrantDetailDrawer } from "@/components/GrantDetailDrawer"
import { CaptureConfigDialog, CaptureConfigValues } from "@/components/CaptureConfigDialog"
import { DateRangePicker, DateRange } from "@/components/DateRangePicker"
import { ActiveFilters } from "@/components/ActiveFilters"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { LayoutGrid, List, Filter, Download, RefreshCw, Send, Database } from "lucide-react"

type ViewMode = "table" | "cards"

export default function GrantsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("table")
  const [grants, setGrants] = useState<Grant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectedGrant, setSelectedGrant] = useState<Grant | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [capturing, setCapturing] = useState(false)
  const [sending, setSending] = useState(false)
  const [captureDialogOpen, setCaptureDialogOpen] = useState(false)
  const [captureSource, setCaptureSource] = useState<"BDNS" | "BOE">("BDNS")

  // Quick filters
  const [quickFilters, setQuickFilters] = useState<QuickFilter[]>([
    { id: "open", label: "Abiertas", active: false },
    { id: "high_budget", label: ">€500k", active: false },
    { id: "nonprofit", label: "Nonprofit", active: false },
    { id: "sent_n8n", label: "Enviados N8n", active: false },
  ])

  // Advanced filters
  const [advancedFilters, setAdvancedFilters] =
    useState<AdvancedFilters>(DEFAULT_FILTERS)

  // Date range filter
  const [dateRange, setDateRange] = useState<DateRange>({ from: null, to: null })

  const API_BASE = "/api/v1"

  // Load grants
  useEffect(() => {
    loadGrants()
  }, [advancedFilters, quickFilters, dateRange])

  const loadGrants = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()

      // Apply date range filter
      if (dateRange.from) params.append("date_from", dateRange.from)
      if (dateRange.to) params.append("date_to", dateRange.to)

      // Apply advanced filters
      if (advancedFilters.search) params.append("search", advancedFilters.search)
      if (advancedFilters.department)
        params.append("department", advancedFilters.department)
      if (advancedFilters.budgetMin > 0)
        params.append("budget_min", advancedFilters.budgetMin.toString())
      if (advancedFilters.budgetMax < 10000000)
        params.append("budget_max", advancedFilters.budgetMax.toString())
      if (advancedFilters.confidenceMin > 0)
        params.append(
          "confidence_min",
          (advancedFilters.confidenceMin / 100).toString()
        )
      if (advancedFilters.source) params.append("source", advancedFilters.source)

      // Apply quick filters
      const activeQuickFilters = quickFilters.filter((f) => f.active)
      activeQuickFilters.forEach((filter) => {
        switch (filter.id) {
          case "open":
            params.append("is_open", "true")
            break
          case "high_budget":
            params.append("budget_min", "500000")
            break
          case "nonprofit":
            params.append("is_nonprofit", "true")
            break
          case "sent_n8n":
            params.append("sent_to_n8n", "true")
            break
        }
      })

      // Apply boolean filters from advanced panel
      if (advancedFilters.isOpen !== null)
        params.append("is_open", advancedFilters.isOpen.toString())
      if (advancedFilters.sentToN8n !== null)
        params.append("sent_to_n8n", advancedFilters.sentToN8n.toString())
      if (advancedFilters.isNonprofit)
        params.append("is_nonprofit", "true")

      params.append("limit", "100")

      const response = await fetch(`${API_BASE}/grants?${params.toString()}`)
      if (!response.ok) throw new Error("Error cargando grants")

      const data: GrantsResponse = await response.json()
      setGrants(data.grants)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido")
    } finally {
      setLoading(false)
    }
  }

  const handleOpenCaptureDialog = (source: "BDNS" | "BOE") => {
    setCaptureSource(source)
    setCaptureDialogOpen(true)
  }

  const handleCapture = async (config: CaptureConfigValues) => {
    setCapturing(true)
    setError(null)
    setCaptureDialogOpen(false)

    try {
      if (captureSource === "BDNS") {
        const response = await fetch(`${API_BASE}/capture/bdns`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date_from: config.date_from,
            date_to: config.date_to,
            max_results: config.max_results || 50
          }),
        })
        if (!response.ok) throw new Error("Error capturando grants de BDNS")
        const result = await response.json()

        const message = `✅ Captura BDNS exitosa!\n\n${result.stats.total_new} nuevos grants\n${result.stats.total_updated} actualizados\n${result.stats.total_nonprofit} nonprofit`
        alert(message)
      } else {
        const response = await fetch(`${API_BASE}/capture/boe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_date: config.target_date || undefined,
            min_relevance: config.min_relevance || 0.3
          }),
        })
        if (!response.ok) throw new Error("Error capturando grants de BOE")
        const result = await response.json()

        const message = `✅ Captura BOE exitosa!\n\n${result.stats.total_scanned} documentos escaneados\n${result.stats.total_new} nuevos grants\n${result.stats.total_updated} actualizados`
        alert(message)
      }

      await loadGrants()
    } catch (err) {
      setError(err instanceof Error ? err.message : `Error capturando ${captureSource}`)
    } finally {
      setCapturing(false)
    }
  }

  const sendToN8n = async () => {
    if (selectedIds.size === 0) {
      alert("⚠️ Selecciona al menos un grant para enviar")
      return
    }

    setSending(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/webhook/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grant_ids: Array.from(selectedIds) }),
      })

      if (response.status === 503) {
        const error = await response.json()
        alert(
          `⚠️ N8n no está configurado\n\n${error.detail}\n\nPor favor, configura N8N_WEBHOOK_URL en las variables de entorno del backend.`
        )
        return
      }

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Error enviando a N8n")
      }

      const result = await response.json()
      alert(`✅ Enviado a N8n!\n\n${result.message}`)
      setSelectedIds(new Set())
      await loadGrants()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error enviando")
    } finally {
      setSending(false)
    }
  }

  const handleQuickFilterToggle = (filterId: string) => {
    setQuickFilters((prev) =>
      prev.map((f) => (f.id === filterId ? { ...f, active: !f.active } : f))
    )
  }

  const handleClearQuickFilters = () => {
    setQuickFilters((prev) => prev.map((f) => ({ ...f, active: false })))
  }

  const handleRemoveQuickFilter = (filterId: string) => {
    setQuickFilters((prev) =>
      prev.map((f) => (f.id === filterId ? { ...f, active: false } : f))
    )
  }

  const handleRemoveAdvancedFilter = (filterKey: string) => {
    setAdvancedFilters((prev) => {
      const updated = { ...prev }
      switch (filterKey) {
        case "search":
          updated.search = ""
          break
        case "department":
          updated.department = ""
          break
        case "budgetMin":
          updated.budgetMin = 0
          break
        case "budgetMax":
          updated.budgetMax = 10000000
          break
        case "confidenceMin":
          updated.confidenceMin = 0
          break
        case "source":
          updated.source = ""
          break
        case "isOpen":
          updated.isOpen = null
          break
        case "sentToN8n":
          updated.sentToN8n = null
          break
        case "isNonprofit":
          updated.isNonprofit = false
          break
      }
      return updated
    })
  }

  const handleClearAllFilters = () => {
    setQuickFilters((prev) => prev.map((f) => ({ ...f, active: false })))
    setAdvancedFilters(DEFAULT_FILTERS)
    setDateRange({ from: null, to: null })
  }

  const handleToggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedIds.size === grants.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(grants.map((g) => g.id)))
    }
  }

  const handleGrantClick = (grant: Grant) => {
    setSelectedGrant(grant)
    setDrawerOpen(true)
  }

  const handleSendIndividual = async (grantId: string) => {
    setSending(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/webhook/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grant_ids: [grantId] }),
      })

      if (response.status === 503) {
        const error = await response.json()
        alert(
          `⚠️ N8n no está configurado\n\n${error.detail}\n\nPor favor, configura N8N_WEBHOOK_URL en las variables de entorno del backend.`
        )
        return
      }

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Error enviando a N8n")
      }

      const result = await response.json()
      alert(`✅ Enviado a N8n!\n\n${result.message}`)
      await loadGrants()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error enviando")
    } finally {
      setSending(false)
    }
  }

  const handleDeleteIndividual = async (grantId: string) => {
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/grants/${grantId}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Error eliminando grant")
      }

      await loadGrants()
      // Remove from selected if it was selected
      const newSelected = new Set(selectedIds)
      newSelected.delete(grantId)
      setSelectedIds(newSelected)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error eliminando")
    }
  }

  const handleExportAll = () => {
    const csv = [
      ["Título", "Organismo", "Presupuesto", "Fecha Fin", "Estado", "Fuente"].join(
        ","
      ),
      ...grants.map((g) =>
        [
          `"${g.title}"`,
          `"${g.department || ""}"`,
          g.budget_amount || 0,
          g.application_end_date || "",
          g.is_open ? "Abierta" : "Cerrada",
          g.source,
        ].join(",")
      ),
    ].join("\n")

    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `grants-all-${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6 max-w-7xl">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <CardTitle className="text-3xl font-bold">
                  Convocatorias
                </CardTitle>
                <p className="text-muted-foreground mt-1">
                  Gestiona y explora subvenciones y grants
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-sm">
                  {grants.length} total
                </Badge>
                {selectedIds.size > 0 && (
                  <Badge variant="default" className="text-sm">
                    {selectedIds.size} seleccionado
                    {selectedIds.size !== 1 ? "s" : ""}
                  </Badge>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => handleOpenCaptureDialog("BDNS")}
                disabled={capturing}
                variant="default"
                className="gap-2"
              >
                <Database className="h-4 w-4" />
                {capturing ? "Capturando..." : "Capturar BDNS"}
              </Button>

              <Button
                onClick={() => handleOpenCaptureDialog("BOE")}
                disabled={capturing}
                variant="default"
                className="gap-2 bg-orange-600 hover:bg-orange-700"
              >
                <Database className="h-4 w-4" />
                {capturing ? "Capturando..." : "Capturar BOE"}
              </Button>

              <Button
                onClick={sendToN8n}
                disabled={sending || selectedIds.size === 0}
                variant="default"
                className="gap-2 bg-green-600 hover:bg-green-700"
              >
                <Send className="h-4 w-4" />
                {sending
                  ? "Enviando..."
                  : `Enviar a N8n (${selectedIds.size})`}
              </Button>

              <Button
                onClick={loadGrants}
                disabled={loading}
                variant="outline"
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Actualizar
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Quick Filters */}
      <QuickFilters
        filters={quickFilters}
        onToggle={handleQuickFilterToggle}
        onClearAll={handleClearQuickFilters}
      />

      {/* Date Range Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">
              Rango de fechas:
            </span>
            <DateRangePicker
              value={dateRange}
              onChange={setDateRange}
              onClear={() => setDateRange({ from: null, to: null })}
            />
          </div>
        </CardContent>
      </Card>

      {/* Active Filters - only show if there are active filters */}
      {(quickFilters.some((f) => f.active) ||
        dateRange.from ||
        dateRange.to ||
        advancedFilters.search ||
        advancedFilters.department ||
        advancedFilters.budgetMin > 0 ||
        advancedFilters.budgetMax < 10000000 ||
        advancedFilters.confidenceMin > 0 ||
        advancedFilters.source ||
        advancedFilters.isOpen !== null ||
        advancedFilters.sentToN8n !== null ||
        advancedFilters.isNonprofit) && (
        <Card>
          <CardContent className="p-4">
            <ActiveFilters
              quickFilters={quickFilters}
              advancedFilters={advancedFilters}
              dateRange={dateRange}
              onRemoveQuickFilter={handleRemoveQuickFilter}
              onRemoveAdvancedFilter={handleRemoveAdvancedFilter}
              onClearDateRange={() => setDateRange({ from: null, to: null })}
              onClearAll={handleClearAllFilters}
            />
          </CardContent>
        </Card>
      )}

      {/* Controls Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AdvancedFilterPanel
                filters={advancedFilters}
                onFiltersChange={setAdvancedFilters}
                onClear={() => setAdvancedFilters(DEFAULT_FILTERS)}
              >
                <Button variant="outline" className="gap-2">
                  <Filter className="h-4 w-4" />
                  Filtros Avanzados
                </Button>
              </AdvancedFilterPanel>

              <Button
                variant="outline"
                size="default"
                onClick={handleExportAll}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Exportar Todo
              </Button>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 border rounded-lg p-1">
              <Button
                variant={viewMode === "table" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("table")}
                className="gap-2"
              >
                <List className="h-4 w-4" />
                Tabla
              </Button>
              <Button
                variant={viewMode === "cards" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("cards")}
                className="gap-2"
              >
                <LayoutGrid className="h-4 w-4" />
                Tarjetas
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4">
            <p className="text-destructive">⚠️ {error}</p>
          </CardContent>
        </Card>
      )}

      {/* Grants Display */}
      {viewMode === "table" ? (
        <GrantsTable
          grants={grants}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onSelectAll={handleSelectAll}
          onGrantClick={handleGrantClick}
          onSendIndividual={handleSendIndividual}
          onDeleteIndividual={handleDeleteIndividual}
          loading={loading}
        />
      ) : (
        <ConvocatoriaGrid
          grants={grants}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onGrantClick={handleGrantClick}
          loading={loading}
        />
      )}

      {/* Grant Detail Drawer */}
      <GrantDetailDrawer
        grant={selectedGrant}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false)
          setSelectedGrant(null)
        }}
      />

      {/* Capture Config Dialog */}
      <CaptureConfigDialog
        open={captureDialogOpen}
        source={captureSource}
        onCapture={handleCapture}
        onCancel={() => setCaptureDialogOpen(false)}
        isCapturing={capturing}
      />
    </div>
  )
}
