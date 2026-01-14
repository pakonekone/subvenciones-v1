import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Grant, GrantsResponse } from "@/types"
import { QuickFilter } from "@/components/QuickFilters"
import {
  AdvancedFilterPanel,
  AdvancedFilters,
  DEFAULT_FILTERS,
} from "@/components/AdvancedFilterPanel"
import { GrantsTable } from "@/components/GrantsTable"
import { ConvocatoriaGrid } from "@/components/ConvocatoriaCard"
import { GrantDetailDrawer } from "@/components/GrantDetailDrawer"
import { CaptureConfigDialog, CaptureConfigValues } from "@/components/CaptureConfigDialog"
import { DateRange } from "@/components/DateRangePicker"
import { ActiveFilters } from "@/components/ActiveFilters"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Database, Download, Heart } from "lucide-react"
import { getApiUrl } from "@/config/api"
import { ControlBar } from "@/components/ControlBar"
import { FloatingActionBar } from "@/components/FloatingActionBar"
import { AlertsPanel } from "@/components/AlertsPanel"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useFavorites } from "@/hooks/useFavorites"

type ViewMode = "table" | "cards"

export default function GrantsPage() {
  const navigate = useNavigate()
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
  const [captureSource, setCaptureSource] = useState<"BDNS" | "BOE" | "PLACSP">("BDNS")
  const [showN8nProcessingBanner, setShowN8nProcessingBanner] = useState(false)
  const [showOnlyFavorites, setShowOnlyFavorites] = useState(false)

  // Favorites hook
  const { favoriteIds, isFavorite, toggleFavorite, favoritesCount } = useFavorites()

  // UI State
  const [activeTab, setActiveTab] = useState("all")
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  // Quick filters
  const [quickFilters, setQuickFilters] = useState<QuickFilter[]>([
    { id: "nonprofit", label: "Nonprofit", active: false },
    { id: "high_budget", label: ">€500k", active: false },
  ])

  // Advanced filters
  const [advancedFilters, setAdvancedFilters] =
    useState<AdvancedFilters>(DEFAULT_FILTERS)

  // Date range filter
  const [dateRange, setDateRange] = useState<DateRange>({ from: null, to: null })
  const [dateField, setDateField] = useState<string>("application_end_date")

  // Load grants
  useEffect(() => {
    loadGrants()
  }, [advancedFilters, quickFilters, dateRange, dateField, activeTab])

  const loadGrants = async () => {
    // Preserve scroll position
    const scrollY = window.scrollY

    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()

      // Apply date range filter
      params.append("date_field", dateField)
      if (dateRange.from) params.append("date_from", dateRange.from)
      if (dateRange.to) params.append("date_to", dateRange.to)

      // Apply Tab filters
      if (activeTab === "open") params.append("is_open", "true")
      if (activeTab === "n8n") params.append("sent_to_n8n", "true")

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
          case "high_budget":
            params.append("budget_min", "500000")
            break
          case "nonprofit":
            params.append("is_nonprofit", "true")
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

      const response = await fetch(getApiUrl(`/api/v1/grants?${params.toString()}`))
      if (!response.ok) throw new Error("Error cargando grants")

      const data: GrantsResponse = await response.json()
      setGrants(data.grants)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido")
    } finally {
      setLoading(false)
      // Restore scroll position after render
      setTimeout(() => window.scrollTo(0, scrollY), 0)
    }
  }

  const handleOpenCaptureDialog = (source: "BDNS" | "BOE" | "PLACSP") => {
    setCaptureSource(source)
    setCaptureDialogOpen(true)
  }

  const handleCapture = async (config: CaptureConfigValues) => {
    setCapturing(true)
    setError(null)
    setCaptureDialogOpen(false)

    try {
      if (captureSource === "BDNS") {
        const response = await fetch(getApiUrl('/api/v1/capture/bdns'), {
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
      } else if (captureSource === "PLACSP") {
        const response = await fetch(getApiUrl('/api/v1/capture/placsp'), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            days_back: config.days_back || 1
          }),
        })
        if (!response.ok) throw new Error("Error capturando licitaciones de PLACSP")
        const result = await response.json()

        const message = `✅ Captura PLACSP exitosa!\n\n${result.stats.total_new} nuevas licitaciones\n${result.stats.total_updated} actualizadas\n${result.stats.total_nonprofit} nonprofit`
        alert(message)
      } else {
        const response = await fetch(getApiUrl('/api/v1/capture/boe'), {
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
      const response = await fetch(getApiUrl('/api/v1/webhook/send'), {
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

      await response.json()
      setSelectedIds(new Set())
      setShowN8nProcessingBanner(true)
      await loadGrants()

      // Hide banner after 30 seconds
      setTimeout(() => setShowN8nProcessingBanner(false), 30000)
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
    // Navigate to grant detail page
    navigate(`/grants/${grant.id}`)
  }

  const handleViewDetails = (grant: Grant) => {
    // Open drawer for quick view (useful in card view)
    setSelectedGrant(grant)
    setDrawerOpen(true)
  }

  const handleSendIndividual = async (grantId: string) => {
    setSending(true)
    setError(null)
    try {
      const response = await fetch(getApiUrl('/api/v1/webhook/send'), {
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

      await response.json()
      setShowN8nProcessingBanner(true)
      await loadGrants()

      // Hide banner after 30 seconds
      setTimeout(() => setShowN8nProcessingBanner(false), 30000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error enviando")
    } finally {
      setSending(false)
    }
  }

  const handleDeleteIndividual = async (grantId: string) => {
    setError(null)
    try {
      const response = await fetch(getApiUrl(`/api/v1/grants/${grantId}`), {
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

  const handleExportSelected = () => {
    const selectedGrants = grants.filter(g => selectedIds.has(g.id))
    const csv = [
      ["Título", "Organismo", "Presupuesto", "Fecha Fin", "Estado", "Fuente"].join(
        ","
      ),
      ...selectedGrants.map((g) =>
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
    a.download = `grants-selected-${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
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

  const hasActiveFilters = !!(
    quickFilters.some((f) => f.active) ||
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
    advancedFilters.isNonprofit
  )

  return (
    <div className="container mx-auto px-4 py-6 space-y-6 max-w-7xl">
      {/* N8n Processing Banner */}
      {showN8nProcessingBanner && (
        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <div>
              <p className="font-semibold text-blue-900 dark:text-blue-100">Grants enviados a N8n</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">Procesando y exportando a Google Sheets... Haz click en "Actualizar" en 10-15 segundos para ver los resultados.</p>
            </div>
          </div>
          <button
            onClick={() => setShowN8nProcessingBanner(false)}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Subvenciones</h1>
          <p className="text-muted-foreground mt-1">
            Base de datos de ayudas capturadas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-sm h-9 px-3">
            {showOnlyFavorites ? `${favoritesCount} favoritos` : `${grants.length} resultados`}
          </Badge>

          <Button
            onClick={() => setShowOnlyFavorites(!showOnlyFavorites)}
            variant={showOnlyFavorites ? "default" : "outline"}
            className={`gap-2 ${showOnlyFavorites ? 'bg-red-500 hover:bg-red-600' : ''}`}
          >
            <Heart className={`h-4 w-4 ${showOnlyFavorites ? 'fill-current' : ''}`} />
            {favoritesCount > 0 && <span>{favoritesCount}</span>}
          </Button>

          <AlertsPanel />

          <Button
            onClick={loadGrants}
            disabled={loading}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>

          <Button
            onClick={handleExportAll}
            variant="outline"
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Exportar CSV
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button className="gap-2">
                <Database className="h-4 w-4" />
                Importar Datos
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleOpenCaptureDialog("BDNS")}>
                Capturar BDNS
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleOpenCaptureDialog("BOE")}>
                Capturar BOE
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleOpenCaptureDialog("PLACSP")}>
                Capturar PLACSP
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Control Bar */}
      <ControlBar
        searchValue={advancedFilters.search}
        onSearchChange={(val) => setAdvancedFilters(prev => ({ ...prev, search: val }))}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        quickFilters={quickFilters}
        onToggleQuickFilter={handleQuickFilterToggle}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        dateField={dateField}
        onDateFieldChange={setDateField}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onToggleAdvancedFilters={() => setShowAdvancedFilters(!showAdvancedFilters)}
        hasActiveAdvancedFilters={hasActiveFilters}
      />

      {/* Advanced Filters Panel (Collapsible) */}
      {showAdvancedFilters && (
        <Card className="bg-muted/30">
          <CardContent className="p-4">
            <AdvancedFilterPanel
              filters={advancedFilters}
              onFiltersChange={setAdvancedFilters}
              onClear={() => setAdvancedFilters(DEFAULT_FILTERS)}
            />
          </CardContent>
        </Card>
      )}

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <ActiveFilters
          quickFilters={quickFilters}
          advancedFilters={advancedFilters}
          dateRange={dateRange}
          onRemoveQuickFilter={handleRemoveQuickFilter}
          onRemoveAdvancedFilter={handleRemoveAdvancedFilter}
          onClearDateRange={() => setDateRange({ from: null, to: null })}
          onClearAll={handleClearAllFilters}
        />
      )}

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
          grants={showOnlyFavorites ? grants.filter(g => favoriteIds.has(g.id)) : grants}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onSelectAll={handleSelectAll}
          onGrantClick={handleGrantClick}
          onViewDetails={handleViewDetails}
          onSendIndividual={handleSendIndividual}
          onDeleteIndividual={handleDeleteIndividual}
          loading={loading}
          favoriteIds={favoriteIds}
          onToggleFavorite={toggleFavorite}
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
        isFavorite={selectedGrant ? isFavorite(selectedGrant.id) : false}
        onToggleFavorite={selectedGrant ? () => toggleFavorite(selectedGrant.id) : undefined}
      />

      {/* Capture Config Dialog */}
      <CaptureConfigDialog
        open={captureDialogOpen}
        source={captureSource}
        onCapture={handleCapture}
        onCancel={() => setCaptureDialogOpen(false)}
        isCapturing={capturing}
      />

      {/* Floating Action Bar */}
      <FloatingActionBar
        selectedCount={selectedIds.size}
        onSendToN8n={sendToN8n}
        onDelete={() => {
          // Bulk delete not implemented in backend yet, but we can iterate or add endpoint
          // For now, let's just alert or implement iteration
          if (confirm(`¿Estás seguro de eliminar ${selectedIds.size} grants?`)) {
            selectedIds.forEach(id => handleDeleteIndividual(id))
          }
        }}
        onExport={handleExportSelected}
        onClearSelection={() => setSelectedIds(new Set())}
        sending={sending}
      />

      </div>
  )
}
