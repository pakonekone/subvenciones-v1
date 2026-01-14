import { Grant } from "@/types"
import { Badge } from "@/components/ui/badge"
import { FavoriteButton } from "@/components/FavoriteButton"
import { CheckCircle2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface GrantHeaderProps {
  grant: Grant
  isFavorite: boolean
  onToggleFavorite: () => Promise<void>
}

export function GrantHeader({ grant, isFavorite, onToggleFavorite }: GrantHeaderProps) {
  const getSourceBadge = (source: string) => {
    const colors: Record<string, string> = {
      BOE: "bg-blue-600",
      BDNS: "bg-green-600",
      PLACSP: "bg-purple-600",
    }
    return (
      <Badge className={cn("text-white", colors[source] || "bg-gray-600")}>
        {source}
      </Badge>
    )
  }

  const getStatusBadge = () => {
    if (grant.is_open) {
      return (
        <Badge variant="default" className="bg-green-500 gap-1">
          <CheckCircle2 className="h-3 w-3" />
          Abierta
        </Badge>
      )
    }
    return (
      <Badge variant="secondary" className="bg-gray-500 text-white gap-1">
        <AlertCircle className="h-3 w-3" />
        Cerrada
      </Badge>
    )
  }

  return (
    <div className="space-y-4 mb-8">
      {/* Title row */}
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight leading-tight">
          {grant.title}
        </h1>
        <FavoriteButton
          isFavorite={isFavorite}
          onToggle={onToggleFavorite}
          size="lg"
          showLabel
          className="shrink-0"
        />
      </div>

      {/* Subtitle and badges */}
      <div className="flex flex-wrap items-center gap-3">
        {grant.department && (
          <span className="text-muted-foreground">{grant.department}</span>
        )}
        {grant.bdns_code && (
          <span className="text-muted-foreground text-sm">
            BDNS-{grant.bdns_code}
          </span>
        )}
      </div>

      {/* Status badges */}
      <div className="flex flex-wrap gap-2">
        {getStatusBadge()}
        {getSourceBadge(grant.source)}
        {grant.sent_to_n8n && (
          <Badge variant="outline" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Enviado a N8n
          </Badge>
        )}
        {grant.nonprofit_confidence && grant.nonprofit_confidence > 0.7 && (
          <Badge variant="outline" className="bg-amber-50 border-amber-300 text-amber-700">
            Nonprofit {Math.round(grant.nonprofit_confidence * 100)}%
          </Badge>
        )}
      </div>
    </div>
  )
}
