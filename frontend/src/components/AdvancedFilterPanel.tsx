import { useState } from "react"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Filter, X } from "lucide-react"

export interface AdvancedFilters {
  search: string
  budgetMin: number
  budgetMax: number
  confidenceMin: number
  department: string
  source: string
  isOpen: boolean | null
  sentToN8n: boolean | null
  isNonprofit: boolean
}

interface AdvancedFilterPanelProps {
  filters: AdvancedFilters
  onFiltersChange: (filters: AdvancedFilters) => void
  onClear: () => void
  children?: React.ReactNode
}

const DEFAULT_FILTERS: AdvancedFilters = {
  search: "",
  budgetMin: 0,
  budgetMax: 10000000,
  confidenceMin: 0,
  department: "",
  source: "",
  isOpen: null,
  sentToN8n: null,
  isNonprofit: false,
}

export function AdvancedFilterPanel({
  filters,
  onFiltersChange,
  onClear,
  children,
}: AdvancedFilterPanelProps) {
  const [localFilters, setLocalFilters] = useState<AdvancedFilters>(filters)
  const [open, setOpen] = useState(false)

  const handleApply = () => {
    onFiltersChange(localFilters)
    setOpen(false)
  }

  const handleClear = () => {
    setLocalFilters(DEFAULT_FILTERS)
    onClear()
    setOpen(false)
  }

  const updateFilter = <K extends keyof AdvancedFilters>(
    key: K,
    value: AdvancedFilters[K]
  ) => {
    setLocalFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        {children || (
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            Filtros Avanzados
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Filtros Avanzados</SheetTitle>
          <SheetDescription>
            Configura filtros detallados para encontrar grants específicos
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 py-6">
          {/* Search */}
          <div className="space-y-2">
            <Label htmlFor="search">Búsqueda de texto</Label>
            <Input
              id="search"
              placeholder="Buscar en título, departamento..."
              value={localFilters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
            />
          </div>

          <Separator />

          {/* Budget Range */}
          <div className="space-y-4">
            <Label>
              Rango de presupuesto:{" "}
              <span className="text-sm text-muted-foreground">
                €{localFilters.budgetMin.toLocaleString()} - €
                {localFilters.budgetMax.toLocaleString()}
              </span>
            </Label>
            <Slider
              min={0}
              max={10000000}
              step={50000}
              value={[localFilters.budgetMin, localFilters.budgetMax]}
              onValueChange={([min, max]) => {
                updateFilter("budgetMin", min)
                updateFilter("budgetMax", max)
              }}
              className="w-full"
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="number"
                placeholder="Min"
                value={localFilters.budgetMin}
                onChange={(e) =>
                  updateFilter("budgetMin", Number(e.target.value))
                }
              />
              <Input
                type="number"
                placeholder="Max"
                value={localFilters.budgetMax}
                onChange={(e) =>
                  updateFilter("budgetMax", Number(e.target.value))
                }
              />
            </div>
          </div>

          <Separator />

          {/* Confidence Slider */}
          <div className="space-y-4">
            <Label>
              Confianza mínima:{" "}
              <span className="text-sm text-muted-foreground">
                {localFilters.confidenceMin}%
              </span>
            </Label>
            <Slider
              min={0}
              max={100}
              step={5}
              value={[localFilters.confidenceMin]}
              onValueChange={([value]) => updateFilter("confidenceMin", value)}
              className="w-full"
            />
          </div>

          <Separator />

          {/* Department */}
          <div className="space-y-2">
            <Label htmlFor="department">Organismo</Label>
            <Input
              id="department"
              placeholder="Ministerio, organismo..."
              value={localFilters.department}
              onChange={(e) => updateFilter("department", e.target.value)}
            />
          </div>

          <Separator />

          {/* Source */}
          <div className="space-y-2">
            <Label htmlFor="source">Fuente</Label>
            <Select
              value={localFilters.source || "ALL"}
              onValueChange={(value) => updateFilter("source", value === "ALL" ? "" : value)}
            >
              <SelectTrigger id="source">
                <SelectValue placeholder="Todas las fuentes" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todas</SelectItem>
                <SelectItem value="BOE">BOE</SelectItem>
                <SelectItem value="BDNS">BDNS</SelectItem>
                <SelectItem value="Nonprofit">Nonprofit</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Separator />

          {/* Toggles */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="isOpen" className="cursor-pointer">
                Solo convocatorias abiertas
              </Label>
              <Switch
                id="isOpen"
                checked={localFilters.isOpen === true}
                onCheckedChange={(checked) =>
                  updateFilter("isOpen", checked ? true : null)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="sentToN8n" className="cursor-pointer">
                Solo enviados a N8n
              </Label>
              <Switch
                id="sentToN8n"
                checked={localFilters.sentToN8n === true}
                onCheckedChange={(checked) =>
                  updateFilter("sentToN8n", checked ? true : null)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="isNonprofit" className="cursor-pointer">
                Solo entidades sin ánimo de lucro
              </Label>
              <Switch
                id="isNonprofit"
                checked={localFilters.isNonprofit}
                onCheckedChange={(checked) =>
                  updateFilter("isNonprofit", checked)
                }
              />
            </div>
          </div>
        </div>

        <SheetFooter className="gap-2">
          <Button variant="outline" onClick={handleClear} className="gap-2">
            <X className="h-4 w-4" />
            Limpiar
          </Button>
          <Button onClick={handleApply}>Aplicar Filtros</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export { DEFAULT_FILTERS }
