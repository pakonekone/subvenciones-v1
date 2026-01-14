import { Grant } from "@/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Calendar, Clock, AlertCircle, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface GrantTimelineProps {
  grant: Grant
}

export function GrantTimeline({ grant }: GrantTimelineProps) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    const date = new Date(dateStr)
    return date.toLocaleDateString("es-ES", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })
  }

  const getDaysRemaining = () => {
    if (!grant.application_end_date || !grant.is_open) return null
    const end = new Date(grant.application_end_date)
    const now = new Date()
    const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    return diff
  }

  const daysRemaining = getDaysRemaining()

  return (
    <Card className="mb-8">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Days remaining alert */}
        {daysRemaining !== null && daysRemaining > 0 && (
          <div className={cn(
            "mb-6 p-4 rounded-lg flex items-center gap-3",
            daysRemaining <= 7 ? "bg-red-50 border border-red-200" :
            daysRemaining <= 30 ? "bg-amber-50 border border-amber-200" :
            "bg-green-50 border border-green-200"
          )}>
            <AlertCircle className={cn(
              "h-5 w-5",
              daysRemaining <= 7 ? "text-red-600" :
              daysRemaining <= 30 ? "text-amber-600" :
              "text-green-600"
            )} />
            <div>
              <p className={cn(
                "font-semibold",
                daysRemaining <= 7 ? "text-red-800" :
                daysRemaining <= 30 ? "text-amber-800" :
                "text-green-800"
              )}>
                {daysRemaining} dias restantes
              </p>
              <p className="text-sm text-muted-foreground">
                Fecha limite: {formatDate(grant.application_end_date)}
              </p>
            </div>
          </div>
        )}

        {/* Timeline visual */}
        <div className="relative space-y-8 before:absolute before:inset-0 before:ml-5 before:h-full before:w-0.5 before:bg-border">
          {/* Publication Date */}
          {grant.publication_date && (
            <div className="relative flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-background">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">Publicacion</p>
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
                <Clock className="h-5 w-5 text-green-600" />
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
                  grant.is_open ? "border-red-500" : "border-muted"
                )}
              >
                <AlertCircle
                  className={cn(
                    "h-5 w-5",
                    grant.is_open ? "text-red-500" : "text-muted-foreground"
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
                {grant.sent_to_n8n ? "Enviado a N8n" : "Pendiente de envio"}
              </p>
              <p className="text-sm text-muted-foreground">
                {grant.sent_to_n8n
                  ? "Procesado por el sistema de analisis"
                  : "Aun no se ha enviado para analisis"}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
