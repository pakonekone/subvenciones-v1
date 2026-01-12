import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Alert, AlertCreate, AlertUpdate, useAlerts } from '@/hooks/useAlerts'
import { AlertConfigDialog } from '@/components/AlertConfigDialog'
import {
  Bell,
  BellRing,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Mail,
  Search,
  Euro,
  Building2,
  CheckCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function AlertsPanel() {
  const {
    alerts,
    isLoading,
    activeAlertsCount,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleAlert
  } = useAlerts()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [sheetOpen, setSheetOpen] = useState(false)

  const handleCreateAlert = () => {
    setEditingAlert(null)
    setDialogOpen(true)
  }

  const handleEditAlert = (alert: Alert) => {
    setEditingAlert(alert)
    setDialogOpen(true)
  }

  const handleSaveAlert = async (data: AlertCreate | AlertUpdate) => {
    setIsSaving(true)
    try {
      if (editingAlert) {
        await updateAlert(editingAlert.id, data as AlertUpdate)
      } else {
        await createAlert(data as AlertCreate)
      }
      setDialogOpen(false)
      setEditingAlert(null)
    } catch (err) {
      console.error('Error saving alert:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteAlert = async (alertId: number) => {
    if (confirm('¿Estás seguro de que quieres eliminar esta alerta?')) {
      try {
        await deleteAlert(alertId)
      } catch (err) {
        console.error('Error deleting alert:', err)
      }
    }
  }

  const handleToggleAlert = async (alertId: number) => {
    try {
      await toggleAlert(alertId)
    } catch (err) {
      console.error('Error toggling alert:', err)
    }
  }

  const formatBudget = (amount: number | null) => {
    if (!amount) return null
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <>
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetTrigger asChild>
          <Button variant="outline" className="gap-2 relative">
            <Bell className="h-4 w-4" />
            Alertas
            {activeAlertsCount > 0 && (
              <Badge
                variant="default"
                className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs bg-primary"
              >
                {activeAlertsCount}
              </Badge>
            )}
          </Button>
        </SheetTrigger>
        <SheetContent className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <BellRing className="h-5 w-5 text-primary" />
              Mis Alertas
            </SheetTitle>
            <SheetDescription>
              Recibe notificaciones cuando aparezcan nuevas subvenciones que coincidan con tus criterios.
            </SheetDescription>
          </SheetHeader>

          <div className="mt-6 space-y-4">
            {/* Create button */}
            <Button onClick={handleCreateAlert} className="w-full gap-2">
              <Plus className="h-4 w-4" />
              Crear nueva alerta
            </Button>

            {/* Alerts list */}
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2].map(i => (
                  <div key={i} className="h-24 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : alerts.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                  <Bell className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    No tienes alertas configuradas.
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Crea una para recibir notificaciones de nuevas subvenciones.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {alerts.map(alert => (
                  <Card
                    key={alert.id}
                    className={cn(
                      'transition-all',
                      !alert.is_active && 'opacity-60'
                    )}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{alert.name}</CardTitle>
                          {alert.is_active ? (
                            <Badge variant="default" className="bg-green-500 text-xs">
                              Activa
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs">
                              Pausada
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={alert.is_active}
                            onCheckedChange={() => handleToggleAlert(alert.id)}
                          />
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleEditAlert(alert)}>
                                <Pencil className="h-4 w-4 mr-2" />
                                Editar
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDeleteAlert(alert.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      {/* Email */}
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                        <Mail className="h-3.5 w-3.5" />
                        {alert.email}
                      </div>

                      {/* Criteria badges */}
                      <div className="flex flex-wrap gap-1.5">
                        {alert.keywords && (
                          <Badge variant="outline" className="text-xs gap-1">
                            <Search className="h-3 w-3" />
                            {alert.keywords.split(',').slice(0, 2).join(', ')}
                            {alert.keywords.split(',').length > 2 && '...'}
                          </Badge>
                        )}
                        {alert.source && (
                          <Badge variant="outline" className="text-xs gap-1">
                            <Building2 className="h-3 w-3" />
                            {alert.source}
                          </Badge>
                        )}
                        {(alert.min_budget || alert.max_budget) && (
                          <Badge variant="outline" className="text-xs gap-1">
                            <Euro className="h-3 w-3" />
                            {alert.min_budget ? formatBudget(alert.min_budget) : '0'}
                            {' - '}
                            {alert.max_budget ? formatBudget(alert.max_budget) : '∞'}
                          </Badge>
                        )}
                        {alert.is_nonprofit && (
                          <Badge variant="outline" className="text-xs gap-1 text-green-600">
                            <CheckCircle className="h-3 w-3" />
                            Nonprofit
                          </Badge>
                        )}
                      </div>

                      {/* Stats */}
                      {alert.matches_count > 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          {alert.matches_count} coincidencias encontradas
                          {alert.last_triggered_at && (
                            <> · Última: {new Date(alert.last_triggered_at).toLocaleDateString('es-ES')}</>
                          )}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Alert Config Dialog */}
      <AlertConfigDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false)
          setEditingAlert(null)
        }}
        onSave={handleSaveAlert}
        alert={editingAlert}
        isSaving={isSaving}
      />
    </>
  )
}
