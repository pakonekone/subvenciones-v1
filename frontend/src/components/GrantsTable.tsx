import { useState, useMemo, useEffect } from "react"
import { Grant } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Download,
  ExternalLink,
  Send,
  Trash2,
  Sheet,
  Clock,
  Minus,
} from "lucide-react"
import { cn } from "@/lib/utils"

type SortField =
  | "title"
  | "department"
  | "budget_amount"
  | "application_end_date"
  | "publication_date"
  | "nonprofit_confidence"

type SortDirection = "asc" | "desc" | null

interface GrantsTableProps {
  grants: Grant[]
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
  onSelectAll: () => void
  onGrantClick: (grant: Grant) => void
  onSendIndividual?: (grantId: string) => void
  onDeleteIndividual?: (grantId: string) => void
  loading?: boolean
}

export function GrantsTable({
  grants,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onGrantClick,
  onSendIndividual,
  onDeleteIndividual,
  loading = false,
}: GrantsTableProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)

  // Handle column sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === "asc") {
        setSortDirection("desc")
      } else if (sortDirection === "desc") {
        setSortDirection(null)
        setSortField(null)
      }
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, grants.length])

  // Filter and sort grants
  const filteredGrants = useMemo(() => {
    let filtered = grants

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = grants.filter(
        (grant) =>
          grant.title.toLowerCase().includes(query) ||
          grant.department?.toLowerCase().includes(query) ||
          grant.bdns_code?.toLowerCase().includes(query)
      )
    }

    // Apply sorting
    if (sortField && sortDirection) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField]
        const bValue = b[sortField]

        // Handle null values
        if (aValue === null) return 1
        if (bValue === null) return -1

        // Compare values
        let comparison = 0
        if (typeof aValue === "string" && typeof bValue === "string") {
          comparison = aValue.localeCompare(bValue)
        } else if (typeof aValue === "number" && typeof bValue === "number") {
          comparison = aValue - bValue
        }

        return sortDirection === "asc" ? comparison : -comparison
      })
    }

    return filtered
  }, [grants, searchQuery, sortField, sortDirection])

  // Apply pagination
  const processedGrants = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage
    const end = start + itemsPerPage
    return filteredGrants.slice(start, end)
  }, [filteredGrants, currentPage, itemsPerPage])

  // Calculate pagination info
  const totalPages = Math.ceil(filteredGrants.length / itemsPerPage)
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, filteredGrants.length)

  // Format helpers
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-"
    return new Date(dateStr).toLocaleDateString("es-ES")
  }

  const formatAmount = (amount: number | null) => {
    if (!amount) return "-"
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const getStatusBadge = (grant: Grant) => {
    if (grant.is_open) {
      return (
        <Badge variant="default" className="bg-status-active">
          Abierta
        </Badge>
      )
    }
    const endDate = grant.application_end_date
      ? new Date(grant.application_end_date)
      : null
    if (endDate && endDate < new Date()) {
      return (
        <Badge variant="secondary" className="bg-status-closed text-white">
          Cerrada
        </Badge>
      )
    }
    return (
      <Badge variant="destructive" className="bg-status-expiring">
        Finalizando
      </Badge>
    )
  }

  const getSourceBadge = (source: string) => {
    const colors = {
      BOE: "bg-source-boe",
      BDNS: "bg-source-bdns",
      Nonprofit: "bg-source-nonprofit",
    }
    return (
      <Badge className={cn("text-white", colors[source as keyof typeof colors] || "")}>
        {source}
      </Badge>
    )
  }

  const getConfidenceBadge = (confidence: number | null) => {
    if (!confidence) return null
    const percentage = Math.round(confidence * 100)
    let variant: "default" | "secondary" | "destructive" = "default"
    if (percentage >= 70) variant = "default"
    else if (percentage >= 40) variant = "secondary"
    else variant = "destructive"

    return <Badge variant={variant}>{percentage}%</Badge>
  }

  const getExportStatus = (grant: Grant) => {
    if (grant.google_sheets_exported) {
      // Exported successfully - show green icon with link
      if (grant.google_sheets_url) {
        return (
          <a
            href={grant.google_sheets_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
            title={`Exportado ${grant.google_sheets_exported_at ? `el ${formatDate(grant.google_sheets_exported_at)}` : ""}`}
            onClick={(e) => e.stopPropagation()}
          >
            <Sheet className="h-4 w-4" />
          </a>
        )
      }
      return (
        <div
          className="inline-flex items-center gap-1 text-green-600 dark:text-green-400"
          title={`Exportado ${grant.google_sheets_exported_at ? `el ${formatDate(grant.google_sheets_exported_at)}` : ""}`}
        >
          <Sheet className="h-4 w-4" />
        </div>
      )
    } else if (grant.sent_to_n8n) {
      // Sent to N8n but not confirmed - amber processing state
      return (
        <div
          className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400"
          title="Procesando..."
        >
          <Clock className="h-4 w-4" />
        </div>
      )
    } else {
      // Not sent yet - gray dash
      return (
        <div className="inline-flex items-center gap-1 text-muted-foreground">
          <Minus className="h-4 w-4" />
        </div>
      )
    }
  }

  // Sort icon component
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="ml-2 h-4 w-4 opacity-40" />
    }
    if (sortDirection === "asc") {
      return <ArrowUp className="ml-2 h-4 w-4" />
    }
    if (sortDirection === "desc") {
      return <ArrowDown className="ml-2 h-4 w-4" />
    }
    return null
  }

  const handleExportSelected = () => {
    const selectedGrants = grants.filter((g) => selectedIds.has(g.id))
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
    a.download = `grants-${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="h-10 w-64 bg-muted animate-pulse rounded"></div>
            <div className="h-9 w-32 bg-muted animate-pulse rounded"></div>
          </div>
          <div className="overflow-x-auto rounded-md border">
            <div className="space-y-3 p-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="h-4 w-4 bg-muted animate-pulse rounded"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 bg-muted animate-pulse rounded"></div>
                    <div className="h-3 w-1/2 bg-muted animate-pulse rounded"></div>
                  </div>
                  <div className="h-4 w-24 bg-muted animate-pulse rounded"></div>
                  <div className="h-4 w-20 bg-muted animate-pulse rounded"></div>
                  <div className="h-6 w-16 bg-muted animate-pulse rounded"></div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-6">
        {/* Header with search and actions */}
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar grants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportSelected}
              disabled={selectedIds.size === 0}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Exportar ({selectedIds.size})
            </Button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr className="border-b">
                <th className="p-3 text-left">
                  <input
                    type="checkbox"
                    checked={
                      selectedIds.size === processedGrants.length &&
                      processedGrants.length > 0
                    }
                    onChange={onSelectAll}
                    className="cursor-pointer"
                  />
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("title")}
                  >
                    Grant
                    <SortIcon field="title" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("department")}
                  >
                    Organismo
                    <SortIcon field="department" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent cursor-default"
                  >
                    Fuente
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("publication_date")}
                  >
                    F. Publicación
                    <SortIcon field="publication_date" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("budget_amount")}
                  >
                    Presupuesto
                    <SortIcon field="budget_amount" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent cursor-default"
                  >
                    Estado
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("application_end_date")}
                  >
                    Fecha Fin
                    <SortIcon field="application_end_date" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent"
                    onClick={() => handleSort("nonprofit_confidence")}
                  >
                    Confianza
                    <SortIcon field="nonprofit_confidence" />
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent cursor-default"
                  >
                    Exportado
                  </Button>
                </th>
                <th className="p-3 text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-0 font-semibold hover:bg-transparent cursor-default"
                  >
                    Acciones
                  </Button>
                </th>
              </tr>
            </thead>
            <tbody>
              {processedGrants.length === 0 ? (
                <tr>
                  <td colSpan={11} className="p-12 text-center text-muted-foreground">
                    {searchQuery
                      ? "No se encontraron grants con esos criterios"
                      : "No hay grants disponibles"}
                  </td>
                </tr>
              ) : (
                processedGrants.map((grant) => (
                  <tr
                    key={grant.id}
                    className="border-b transition-colors hover:bg-muted/50 cursor-pointer"
                    onClick={() => onGrantClick(grant)}
                  >
                    <td className="p-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(grant.id)}
                        onChange={() => onToggleSelect(grant.id)}
                        className="cursor-pointer"
                      />
                    </td>
                    <td className="p-3">
                      <div
                        className="font-medium max-w-md truncate"
                        title={grant.title}
                      >
                        {grant.title}
                      </div>
                      {grant.bdns_code && (
                        <div className="text-xs text-muted-foreground mt-1">
                          BDNS: {grant.bdns_code}
                        </div>
                      )}
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      <div
                        className="max-w-xs truncate"
                        title={grant.department || undefined}
                      >
                        {grant.department || "-"}
                      </div>
                    </td>
                    <td className="p-3">{getSourceBadge(grant.source)}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      <div title={grant.publication_date || undefined}>
                        {formatDate(grant.publication_date)}
                      </div>
                    </td>
                    <td className="p-3 font-semibold text-success">
                      {formatAmount(grant.budget_amount)}
                    </td>
                    <td className="p-3">{getStatusBadge(grant)}</td>
                    <td className="p-3 text-sm">
                      {formatDate(grant.application_end_date)}
                    </td>
                    <td className="p-3">{getConfidenceBadge(grant.nonprofit_confidence)}</td>
                    <td className="p-3">{getExportStatus(grant)}</td>
                    <td className="p-3" onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-1">
                        {!grant.sent_to_n8n && onSendIndividual && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 hover:bg-green-100 dark:hover:bg-green-900"
                            onClick={() => onSendIndividual(grant.id)}
                            title="Enviar a N8n"
                          >
                            <Send className="h-4 w-4 text-green-600 dark:text-green-400" />
                          </Button>
                        )}
                        {onDeleteIndividual && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 hover:bg-red-100 dark:hover:bg-red-900"
                            onClick={() => {
                              if (confirm(`¿Eliminar "${grant.title}"?`)) {
                                onDeleteIndividual(grant.id)
                              }
                            }}
                            title="Eliminar grant"
                          >
                            <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
                          </Button>
                        )}
                        {grant.regulatory_base_url && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            asChild
                          >
                            <a
                              href={grant.regulatory_base_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Bases Reguladoras"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                        {grant.bdns_code && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            asChild
                          >
                            <a
                              href={`https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/${grant.bdns_code}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Ver en BDNS"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer with pagination and counts */}
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-muted-foreground">
            Mostrando {filteredGrants.length > 0 ? startItem : 0} - {endItem} de {filteredGrants.length}
            {searchQuery && ` (filtrado por "${searchQuery}")`}
            {selectedIds.size > 0 && ` • ${selectedIds.size} seleccionado${selectedIds.size !== 1 ? "s" : ""}`}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Anterior
              </Button>

              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(pageNum)}
                      className="w-9"
                    >
                      {pageNum}
                    </Button>
                  )
                })}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Siguiente
              </Button>

              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value))
                  setCurrentPage(1)
                }}
                className="ml-2 rounded-md border border-input bg-background px-2 py-1 text-sm"
              >
                <option value={10}>10 / página</option>
                <option value={25}>25 / página</option>
                <option value={50}>50 / página</option>
                <option value={100}>100 / página</option>
              </select>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
