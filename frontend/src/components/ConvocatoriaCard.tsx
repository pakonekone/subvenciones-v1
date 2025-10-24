import { Grant } from "@/types"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Calendar,
  Building2,
  Euro,
  ExternalLink,
  Clock,
  CheckCircle2,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ConvocatoriaCardProps {
  grant: Grant
  selected: boolean
  onToggleSelect: (id: string) => void
  onClick: (grant: Grant) => void
}

export function ConvocatoriaCard({
  grant,
  selected,
  onToggleSelect,
  onClick,
}: ConvocatoriaCardProps) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "No especificada"
    const date = new Date(dateStr)
    return date.toLocaleDateString("es-ES", {
      day: "numeric",
      month: "short",
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

  const getDaysRemaining = (endDate: string | null) => {
    if (!endDate) return null
    const end = new Date(endDate)
    const now = new Date()
    const diffTime = end.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const daysRemaining = getDaysRemaining(grant.application_end_date)

  const getDeadlineBadge = () => {
    if (!daysRemaining) return null

    if (daysRemaining < 0) {
      return (
        <Badge variant="secondary" className="gap-1 bg-status-closed text-white">
          <Clock className="h-3 w-3" />
          Cerrada
        </Badge>
      )
    }

    if (daysRemaining <= 7) {
      return (
        <Badge variant="destructive" className="gap-1 bg-status-expiring">
          <Clock className="h-3 w-3" />
          {daysRemaining} días
        </Badge>
      )
    }

    if (daysRemaining <= 30) {
      return (
        <Badge variant="secondary" className="gap-1">
          <Clock className="h-3 w-3" />
          {daysRemaining} días
        </Badge>
      )
    }

    return (
      <Badge variant="default" className="gap-1 bg-status-active">
        <Clock className="h-3 w-3" />
        {daysRemaining} días
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

  const getConfidenceBadge = () => {
    if (!grant.nonprofit_confidence) return null
    const percentage = Math.round(grant.nonprofit_confidence * 100)
    let variant: "default" | "secondary" | "destructive" = "default"
    if (percentage >= 70) variant = "default"
    else if (percentage >= 40) variant = "secondary"
    else variant = "destructive"

    return (
      <Badge variant={variant} className="gap-1">
        <CheckCircle2 className="h-3 w-3" />
        {percentage}%
      </Badge>
    )
  }

  return (
    <Card
      className={cn(
        "group cursor-pointer transition-all hover:shadow-lg hover:border-primary",
        selected && "border-primary shadow-md"
      )}
      onClick={() => onClick(grant)}
    >
      <CardHeader className="space-y-3">
        {/* Header with checkbox and badges */}
        <div className="flex items-start justify-between gap-2">
          <div
            className="flex items-center"
            onClick={(e) => {
              e.stopPropagation()
              onToggleSelect(grant.id)
            }}
          >
            <input
              type="checkbox"
              checked={selected}
              onChange={() => {}}
              className="h-4 w-4 cursor-pointer"
            />
          </div>
          <div className="flex flex-wrap gap-2 justify-end">
            {getDeadlineBadge()}
            {getSourceBadge(grant.source)}
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold leading-tight text-lg line-clamp-2 group-hover:text-primary transition-colors">
          {grant.title}
        </h3>

        {/* Department */}
        {grant.department && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4 flex-shrink-0" />
            <span className="line-clamp-1">{grant.department}</span>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Budget Amount */}
        {grant.budget_amount && (
          <div className="flex items-center gap-2">
            <Euro className="h-4 w-4 text-success flex-shrink-0" />
            <span className="font-semibold text-success">
              {formatAmount(grant.budget_amount)}
            </span>
          </div>
        )}

        {/* Dates */}
        <div className="space-y-2 text-sm">
          {grant.publication_date && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="h-4 w-4 flex-shrink-0" />
              <span>Publicado: {formatDate(grant.publication_date)}</span>
            </div>
          )}
          {grant.application_end_date && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="h-4 w-4 flex-shrink-0" />
              <span>Cierre: {formatDate(grant.application_end_date)}</span>
            </div>
          )}
        </div>

        {/* Beneficiaries */}
        {grant.beneficiary_types && grant.beneficiary_types.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {grant.beneficiary_types.slice(0, 3).map((type, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {type}
              </Badge>
            ))}
            {grant.beneficiary_types.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{grant.beneficiary_types.length - 3}
              </Badge>
            )}
          </div>
        )}

        {/* Confidence and BDNS Code */}
        <div className="flex items-center justify-between">
          {getConfidenceBadge()}
          {grant.bdns_code && (
            <span className="text-xs text-muted-foreground font-mono">
              {grant.bdns_code}
            </span>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        {grant.regulatory_base_url && (
          <Button
            variant="outline"
            size="sm"
            className="flex-1 gap-2"
            onClick={(e) => {
              e.stopPropagation()
              window.open(grant.regulatory_base_url!, "_blank")
            }}
          >
            <ExternalLink className="h-3 w-3" />
            Bases
          </Button>
        )}
        {grant.electronic_office && (
          <Button
            variant="outline"
            size="sm"
            className="flex-1 gap-2"
            onClick={(e) => {
              e.stopPropagation()
              window.open(grant.electronic_office!, "_blank")
            }}
          >
            <ExternalLink className="h-3 w-3" />
            Sede
          </Button>
        )}
        {grant.bdns_code && (
          <Button
            variant="outline"
            size="sm"
            className="flex-1 gap-2"
            onClick={(e) => {
              e.stopPropagation()
              window.open(
                `https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/${grant.bdns_code}`,
                "_blank"
              )
            }}
          >
            <ExternalLink className="h-3 w-3" />
            BDNS
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}

// Grid container component
interface ConvocatoriaGridProps {
  grants: Grant[]
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
  onGrantClick: (grant: Grant) => void
  loading?: boolean
}

export function ConvocatoriaGrid({
  grants,
  selectedIds,
  onToggleSelect,
  onGrantClick,
  loading = false,
}: ConvocatoriaGridProps) {
  if (loading) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        Cargando grants...
      </div>
    )
  }

  if (grants.length === 0) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        No hay grants disponibles
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {grants.map((grant) => (
        <ConvocatoriaCard
          key={grant.id}
          grant={grant}
          selected={selectedIds.has(grant.id)}
          onToggleSelect={onToggleSelect}
          onClick={onGrantClick}
        />
      ))}
    </div>
  )
}
