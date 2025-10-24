import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Calendar, X } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export interface DateRange {
  from: string | null
  to: string | null
}

interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
  onClear: () => void
}

export function DateRangePicker({ value, onChange, onClear }: DateRangePickerProps) {
  const [open, setOpen] = useState(false)

  const presets = [
    {
      label: "Hoy",
      getValue: () => {
        const today = new Date().toISOString().split("T")[0]
        return { from: today, to: today }
      },
    },
    {
      label: "Últimos 7 días",
      getValue: () => {
        const today = new Date()
        const weekAgo = new Date(today)
        weekAgo.setDate(today.getDate() - 7)
        return {
          from: weekAgo.toISOString().split("T")[0],
          to: today.toISOString().split("T")[0],
        }
      },
    },
    {
      label: "Últimos 30 días",
      getValue: () => {
        const today = new Date()
        const monthAgo = new Date(today)
        monthAgo.setDate(today.getDate() - 30)
        return {
          from: monthAgo.toISOString().split("T")[0],
          to: today.toISOString().split("T")[0],
        }
      },
    },
    {
      label: "Próximos 30 días",
      getValue: () => {
        const today = new Date()
        const monthAhead = new Date(today)
        monthAhead.setDate(today.getDate() + 30)
        return {
          from: today.toISOString().split("T")[0],
          to: monthAhead.toISOString().split("T")[0],
        }
      },
    },
  ]

  const handlePreset = (preset: typeof presets[0]) => {
    onChange(preset.getValue())
    setOpen(false)
  }

  const handleCustomChange = (field: "from" | "to", dateValue: string) => {
    onChange({
      ...value,
      [field]: dateValue || null,
    })
  }

  const formatDateRange = () => {
    if (!value.from && !value.to) return "Seleccionar fechas"

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      })
    }

    if (value.from && value.to) {
      if (value.from === value.to) {
        return formatDate(value.from)
      }
      return `${formatDate(value.from)} - ${formatDate(value.to)}`
    }

    if (value.from) return `Desde ${formatDate(value.from)}`
    if (value.to) return `Hasta ${formatDate(value.to)}`

    return "Seleccionar fechas"
  }

  const hasValue = value.from || value.to

  return (
    <div className="flex items-center gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="gap-2 min-w-[200px] justify-start">
            <Calendar className="h-4 w-4" />
            <span className="flex-1 text-left">{formatDateRange()}</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Card className="border-0 shadow-none">
            <CardContent className="p-4 space-y-4">
              {/* Presets */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold">Preselecciones</Label>
                <div className="grid grid-cols-2 gap-2">
                  {presets.map((preset) => (
                    <Button
                      key={preset.label}
                      variant="outline"
                      size="sm"
                      onClick={() => handlePreset(preset)}
                      className="justify-start"
                    >
                      {preset.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Custom Range */}
              <div className="space-y-3 pt-3 border-t">
                <Label className="text-sm font-semibold">Rango personalizado</Label>
                <div className="space-y-2">
                  <div>
                    <Label htmlFor="date-from" className="text-xs">
                      Desde
                    </Label>
                    <Input
                      id="date-from"
                      type="date"
                      value={value.from || ""}
                      onChange={(e) => handleCustomChange("from", e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="date-to" className="text-xs">
                      Hasta
                    </Label>
                    <Input
                      id="date-to"
                      type="date"
                      value={value.to || ""}
                      onChange={(e) => handleCustomChange("to", e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    onClear()
                    setOpen(false)
                  }}
                >
                  Limpiar
                </Button>
                <Button size="sm" onClick={() => setOpen(false)}>
                  Aplicar
                </Button>
              </div>
            </CardContent>
          </Card>
        </PopoverContent>
      </Popover>

      {hasValue && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClear}
          className="h-8 w-8 p-0"
          title="Limpiar fechas"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}
