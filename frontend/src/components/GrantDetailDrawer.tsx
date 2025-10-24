import { Grant } from "@/types"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Calendar,
  Euro,
  ExternalLink,
  Users,
  MapPin,
  Briefcase,
  FileText,
  Clock,
  Bot,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface GrantDetailDrawerProps {
  grant: Grant | null
  open: boolean
  onClose: () => void
}

export function GrantDetailDrawer({ grant, open, onClose }: GrantDetailDrawerProps) {
  if (!grant) return null

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "No especificada"
    const date = new Date(dateStr)
    return date.toLocaleDateString("es-ES", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })
  }

  const formatAmount = (amount: number | null) => {
    if (!amount) return "No especificado"
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(amount)
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

  const getStatusBadge = () => {
    if (grant.is_open) {
      return (
        <Badge variant="default" className="bg-status-active gap-1">
          <CheckCircle2 className="h-3 w-3" />
          Abierta
        </Badge>
      )
    }
    return (
      <Badge variant="secondary" className="bg-status-closed text-white gap-1">
        <AlertCircle className="h-3 w-3" />
        Cerrada
      </Badge>
    )
  }

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <SheetTitle className="text-2xl leading-tight pr-8">
              {grant.title}
            </SheetTitle>
          </div>

          <div className="flex flex-wrap gap-2">
            {getStatusBadge()}
            {getSourceBadge(grant.source)}
            {grant.sent_to_n8n && (
              <Badge variant="outline" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Enviado a N8n
              </Badge>
            )}
          </div>

          {grant.department && (
            <SheetDescription className="text-base">
              {grant.department}
            </SheetDescription>
          )}
        </SheetHeader>

        <Tabs defaultValue="details" className="mt-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="details" className="gap-2">
              <FileText className="h-4 w-4" />
              Detalles
            </TabsTrigger>
            <TabsTrigger value="timeline" className="gap-2">
              <Clock className="h-4 w-4" />
              Timeline
            </TabsTrigger>
            <TabsTrigger value="ai" className="gap-2">
              <Bot className="h-4 w-4" />
              Análisis AI
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Details */}
          <TabsContent value="details" className="space-y-6 mt-6">
            {/* Budget */}
            {grant.budget_amount && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Euro className="h-4 w-4" />
                  Presupuesto
                </div>
                <p className="text-2xl font-bold text-success">
                  {formatAmount(grant.budget_amount)}
                </p>
              </div>
            )}

            <Separator />

            {/* Purpose */}
            {grant.purpose && (
              <>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Briefcase className="h-4 w-4" />
                    Finalidad
                  </div>
                  <p className="text-sm leading-relaxed">{grant.purpose}</p>
                </div>
                <Separator />
              </>
            )}

            {/* Beneficiaries */}
            {grant.beneficiary_types && grant.beneficiary_types.length > 0 && (
              <>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Users className="h-4 w-4" />
                    Beneficiarios
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {grant.beneficiary_types.map((type, index) => (
                      <Badge key={index} variant="secondary">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Sectors */}
            {grant.sectors && grant.sectors.length > 0 && (
              <>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Briefcase className="h-4 w-4" />
                    Sectores
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {grant.sectors.map((sector, index) => (
                      <Badge key={index} variant="outline">
                        {sector}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Regions */}
            {grant.regions && grant.regions.length > 0 && (
              <>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    Regiones
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {grant.regions.map((region, index) => (
                      <Badge key={index} variant="outline">
                        {region}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Confidence Score */}
            {grant.nonprofit_confidence !== null && (
              <>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <CheckCircle2 className="h-4 w-4" />
                    Confianza Nonprofit
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{
                          width: `${grant.nonprofit_confidence * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(grant.nonprofit_confidence * 100)}%
                    </span>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Links */}
            <div className="space-y-3">
              <div className="text-sm font-medium text-muted-foreground">
                Enlaces útiles
              </div>
              <div className="flex flex-col gap-2">
                {grant.regulatory_base_url && (
                  <Button
                    variant="outline"
                    className="justify-start gap-2"
                    asChild
                  >
                    <a
                      href={grant.regulatory_base_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Bases Reguladoras
                    </a>
                  </Button>
                )}
                {grant.electronic_office && (
                  <Button
                    variant="outline"
                    className="justify-start gap-2"
                    asChild
                  >
                    <a
                      href={grant.electronic_office}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Sede Electrónica
                    </a>
                  </Button>
                )}
                {grant.bdns_code && (
                  <Button
                    variant="outline"
                    className="justify-start gap-2"
                    asChild
                  >
                    <a
                      href={`https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/${grant.bdns_code}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Ver en BDNS ({grant.bdns_code})
                    </a>
                  </Button>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Tab 2: Timeline */}
          <TabsContent value="timeline" className="space-y-6 mt-6">
            <div className="relative space-y-8 before:absolute before:inset-0 before:ml-5 before:h-full before:w-0.5 before:bg-border">
              {/* Publication Date */}
              {grant.publication_date && (
                <div className="relative flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-background">
                    <Calendar className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Publicación</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(grant.publication_date)}
                    </p>
                  </div>
                </div>
              )}

              {/* Application Start */}
              {grant.application_start_date && (
                <div className="relative flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-background">
                    <Clock className="h-5 w-5 text-success" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Apertura de plazo</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(grant.application_start_date)}
                    </p>
                  </div>
                </div>
              )}

              {/* Application End */}
              {grant.application_end_date && (
                <div className="relative flex items-start gap-4">
                  <div
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-background",
                      grant.is_open ? "border-destructive" : "border-muted"
                    )}
                  >
                    <AlertCircle
                      className={cn(
                        "h-5 w-5",
                        grant.is_open ? "text-destructive" : "text-muted-foreground"
                      )}
                    />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">
                      {grant.is_open ? "Cierre de plazo" : "Cerrada"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(grant.application_end_date)}
                    </p>
                  </div>
                </div>
              )}

              {/* N8n Status */}
              <div className="relative flex items-start gap-4">
                <div
                  className={cn(
                    "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-background",
                    grant.sent_to_n8n ? "border-primary" : "border-muted"
                  )}
                >
                  <CheckCircle2
                    className={cn(
                      "h-5 w-5",
                      grant.sent_to_n8n ? "text-primary" : "text-muted-foreground"
                    )}
                  />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">
                    {grant.sent_to_n8n ? "Enviado a N8n" : "Pendiente de envío"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {grant.sent_to_n8n
                      ? "Procesado por el sistema de análisis"
                      : "Aún no se ha enviado para análisis"}
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Tab 3: AI Analysis */}
          <TabsContent value="ai" className="space-y-6 mt-6">
            <div className="rounded-lg border bg-muted/50 p-6 text-center">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="font-semibold mb-2">Análisis AI no disponible</h3>
              <p className="text-sm text-muted-foreground mb-4">
                El análisis mediante inteligencia artificial estará disponible próximamente.
              </p>
              {!grant.sent_to_n8n && (
                <p className="text-xs text-muted-foreground">
                  Esta convocatoria debe ser enviada a N8n primero para habilitar el
                  análisis AI.
                </p>
              )}
            </div>

            {grant.sent_to_n8n && (
              <div className="space-y-4">
                <div className="rounded-lg border p-4">
                  <p className="text-sm font-medium mb-2">Estado del análisis</p>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                    <span className="text-sm text-muted-foreground">
                      En cola de procesamiento
                    </span>
                  </div>
                </div>

                <div className="text-xs text-muted-foreground">
                  Una vez procesado, aquí aparecerá:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Resumen ejecutivo generado por AI</li>
                    <li>Puntos clave de la convocatoria</li>
                    <li>Requisitos principales</li>
                    <li>Recomendaciones personalizadas</li>
                  </ul>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  )
}
