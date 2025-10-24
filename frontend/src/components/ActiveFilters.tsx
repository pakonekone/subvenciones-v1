import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { AdvancedFilters } from "./AdvancedFilterPanel"
import { QuickFilter } from "./QuickFilters"
import { DateRange } from "./DateRangePicker"

interface ActiveFiltersProps {
  quickFilters: QuickFilter[]
  advancedFilters: AdvancedFilters
  dateRange: DateRange
  onRemoveQuickFilter: (filterId: string) => void
  onRemoveAdvancedFilter: (filterKey: string) => void
  onClearDateRange: () => void
  onClearAll: () => void
}

export function ActiveFilters({
  quickFilters,
  advancedFilters,
  dateRange,
  onRemoveQuickFilter,
  onRemoveAdvancedFilter,
  onClearDateRange,
  onClearAll,
}: ActiveFiltersProps) {
  const activeQuickFilters = quickFilters.filter((f) => f.active)

  const advancedFiltersList: Array<{ key: string; label: string; value: string }> = []

  if (advancedFilters.search) {
    advancedFiltersList.push({
      key: "search",
      label: "Búsqueda",
      value: advancedFilters.search,
    })
  }

  if (advancedFilters.department) {
    advancedFiltersList.push({
      key: "department",
      label: "Organismo",
      value: advancedFilters.department,
    })
  }

  if (advancedFilters.budgetMin > 0) {
    advancedFiltersList.push({
      key: "budgetMin",
      label: "Presupuesto mín",
      value: `€${advancedFilters.budgetMin.toLocaleString("es-ES")}`,
    })
  }

  if (advancedFilters.budgetMax < 10000000) {
    advancedFiltersList.push({
      key: "budgetMax",
      label: "Presupuesto máx",
      value: `€${advancedFilters.budgetMax.toLocaleString("es-ES")}`,
    })
  }

  if (advancedFilters.confidenceMin > 0) {
    advancedFiltersList.push({
      key: "confidenceMin",
      label: "Confianza mín",
      value: `${advancedFilters.confidenceMin}%`,
    })
  }

  if (advancedFilters.source) {
    advancedFiltersList.push({
      key: "source",
      label: "Fuente",
      value: advancedFilters.source,
    })
  }

  if (advancedFilters.isOpen !== null) {
    advancedFiltersList.push({
      key: "isOpen",
      label: "Estado",
      value: advancedFilters.isOpen ? "Abierta" : "Cerrada",
    })
  }

  if (advancedFilters.sentToN8n !== null) {
    advancedFiltersList.push({
      key: "sentToN8n",
      label: "Enviado N8n",
      value: advancedFilters.sentToN8n ? "Sí" : "No",
    })
  }

  if (advancedFilters.isNonprofit) {
    advancedFiltersList.push({
      key: "isNonprofit",
      label: "Nonprofit",
      value: "Sí",
    })
  }

  const hasDateRange = dateRange.from || dateRange.to

  const totalActiveFilters =
    activeQuickFilters.length +
    advancedFiltersList.length +
    (hasDateRange ? 1 : 0)

  if (totalActiveFilters === 0) {
    return null
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm font-medium text-muted-foreground">
        Filtros activos ({totalActiveFilters}):
      </span>

      {/* Quick Filters */}
      {activeQuickFilters.map((filter) => (
        <Badge
          key={filter.id}
          variant="secondary"
          className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
        >
          <span>{filter.label}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveQuickFilter(filter.id)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {/* Date Range */}
      {hasDateRange && (
        <Badge
          variant="secondary"
          className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
        >
          <span>
            Fecha:{" "}
            {dateRange.from && dateRange.to
              ? `${formatDate(dateRange.from)} - ${formatDate(dateRange.to)}`
              : dateRange.from
              ? `Desde ${formatDate(dateRange.from)}`
              : `Hasta ${formatDate(dateRange.to!)}`}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={onClearDateRange}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      )}

      {/* Advanced Filters */}
      {advancedFiltersList.map((filter) => (
        <Badge
          key={filter.key}
          variant="secondary"
          className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
        >
          <span>
            {filter.label}: {filter.value}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveAdvancedFilter(filter.key)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {/* Clear All */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onClearAll}
        className="h-7 text-xs"
      >
        Limpiar todo
      </Button>
    </div>
  )
}
