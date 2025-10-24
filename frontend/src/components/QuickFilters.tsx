import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

export interface QuickFilter {
  id: string
  label: string
  active: boolean
}

interface QuickFiltersProps {
  filters: QuickFilter[]
  onToggle: (filterId: string) => void
  onClearAll: () => void
}

export function QuickFilters({ filters, onToggle, onClearAll }: QuickFiltersProps) {
  const activeCount = filters.filter(f => f.active).length

  return (
    <div className="flex flex-wrap items-center gap-2 p-4 bg-muted/50 rounded-lg border border-border">
      <span className="text-sm font-medium text-muted-foreground mr-2">
        Filtros rápidos:
      </span>

      {filters.map((filter) => (
        <Button
          key={filter.id}
          variant={filter.active ? "default" : "outline"}
          size="sm"
          onClick={() => onToggle(filter.id)}
          className="gap-2"
        >
          {filter.label}
          {filter.active && <X className="h-3 w-3" />}
        </Button>
      ))}

      {activeCount > 0 && (
        <Badge variant="secondary" className="ml-2">
          {activeCount} activo{activeCount !== 1 ? 's' : ''}
        </Badge>
      )}

      {activeCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="ml-auto text-muted-foreground hover:text-foreground"
        >
          Limpiar todos
        </Button>
      )}
    </div>
  )
}
