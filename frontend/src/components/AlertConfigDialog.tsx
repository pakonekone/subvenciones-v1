import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertCreate, AlertUpdate } from '@/hooks/useAlerts'
import { Bell, Mail, Search, Euro, Building2 } from 'lucide-react'

interface AlertConfigDialogProps {
  open: boolean
  onClose: () => void
  onSave: (data: AlertCreate | AlertUpdate) => Promise<void>
  alert?: Alert | null  // If provided, we're editing
  isSaving?: boolean
}

export function AlertConfigDialog({
  open,
  onClose,
  onSave,
  alert,
  isSaving = false
}: AlertConfigDialogProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [keywords, setKeywords] = useState('')
  const [source, setSource] = useState<string>('')
  const [minBudget, setMinBudget] = useState<string>('')
  const [maxBudget, setMaxBudget] = useState<string>('')
  const [isNonprofit, setIsNonprofit] = useState(false)

  const isEditing = !!alert

  // Initialize form when alert changes
  useEffect(() => {
    if (alert) {
      setName(alert.name)
      setEmail(alert.email)
      setKeywords(alert.keywords || '')
      setSource(alert.source || '')
      setMinBudget(alert.min_budget?.toString() || '')
      setMaxBudget(alert.max_budget?.toString() || '')
      setIsNonprofit(alert.is_nonprofit || false)
    } else {
      // Reset form for new alert
      setName('')
      setEmail('')
      setKeywords('')
      setSource('')
      setMinBudget('')
      setMaxBudget('')
      setIsNonprofit(false)
    }
  }, [alert, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const data: AlertCreate | AlertUpdate = {
      name,
      email,
      keywords: keywords || undefined,
      source: source || undefined,
      min_budget: minBudget ? parseFloat(minBudget) : undefined,
      max_budget: maxBudget ? parseFloat(maxBudget) : undefined,
      is_nonprofit: isNonprofit || undefined,
    }

    await onSave(data)
  }

  const isValid = name.trim() && email.trim() && email.includes('@')

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" />
              {isEditing ? 'Editar Alerta' : 'Nueva Alerta'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Modifica los criterios de tu alerta.'
                : 'Configura los criterios para recibir notificaciones cuando aparezcan nuevas subvenciones.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">Nombre de la alerta *</Label>
              <Input
                id="name"
                placeholder="Ej: Subvenciones cultura Madrid"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            {/* Email */}
            <div className="grid gap-2">
              <Label htmlFor="email" className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Email para notificaciones *
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Keywords */}
            <div className="grid gap-2">
              <Label htmlFor="keywords" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                Palabras clave
              </Label>
              <Input
                id="keywords"
                placeholder="Ej: cultura, educación, medio ambiente"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Separa las palabras clave por comas. Se buscarán en el título y descripción.
              </p>
            </div>

            {/* Source */}
            <div className="grid gap-2">
              <Label htmlFor="source" className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Fuente
              </Label>
              <Select value={source || "any"} onValueChange={(val) => setSource(val === "any" ? "" : val)}>
                <SelectTrigger>
                  <SelectValue placeholder="Cualquier fuente" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Cualquier fuente</SelectItem>
                  <SelectItem value="BDNS">BDNS</SelectItem>
                  <SelectItem value="BOE">BOE</SelectItem>
                  <SelectItem value="PLACSP">PLACSP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Budget Range */}
            <div className="grid gap-2">
              <Label className="flex items-center gap-2">
                <Euro className="h-4 w-4" />
                Rango de presupuesto
              </Label>
              <div className="flex gap-2 items-center">
                <Input
                  type="number"
                  placeholder="Mínimo"
                  value={minBudget}
                  onChange={(e) => setMinBudget(e.target.value)}
                  className="flex-1"
                />
                <span className="text-muted-foreground">-</span>
                <Input
                  type="number"
                  placeholder="Máximo"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="flex-1"
                />
              </div>
            </div>

            {/* Nonprofit filter */}
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="nonprofit">Solo subvenciones nonprofit</Label>
                <p className="text-xs text-muted-foreground">
                  Filtra solo ayudas para entidades sin ánimo de lucro
                </p>
              </div>
              <Switch
                id="nonprofit"
                checked={isNonprofit}
                onCheckedChange={setIsNonprofit}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!isValid || isSaving}>
              {isSaving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear alerta'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
