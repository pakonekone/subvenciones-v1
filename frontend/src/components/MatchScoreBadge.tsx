import { cn } from "@/lib/utils"
import { MatchScore } from "@/types"
import { CheckCircle, AlertCircle, XCircle } from "lucide-react"

interface MatchScoreBadgeProps {
  score: MatchScore
  size?: "sm" | "md" | "lg"
}

export function MatchScoreBadge({
  score,
  size = "sm",
}: MatchScoreBadgeProps) {
  const getColor = () => {
    if (score.total_score >= 70) return "bg-green-500 hover:bg-green-600"
    if (score.total_score >= 40) return "bg-yellow-500 hover:bg-yellow-600"
    return "bg-red-500 hover:bg-red-600"
  }

  const getIcon = () => {
    if (score.recommendation === "APLICAR") {
      return <CheckCircle className="h-3 w-3" />
    }
    if (score.recommendation === "REVISAR") {
      return <AlertCircle className="h-3 w-3" />
    }
    return <XCircle className="h-3 w-3" />
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 gap-1",
    md: "text-sm px-2.5 py-1 gap-1.5",
    lg: "text-base px-3 py-1.5 gap-2",
  }

  // Build tooltip text
  const tooltipText = `${score.recommendation}
Beneficiario: ${score.breakdown.beneficiary_type}%
Sectores: ${score.breakdown.sectors}%
Regiones: ${score.breakdown.regions}%
Presupuesto: ${score.breakdown.budget}%`

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full text-white font-medium transition-colors cursor-default",
        getColor(),
        sizeClasses[size]
      )}
      title={tooltipText}
    >
      {getIcon()}
      {score.total_score}%
    </div>
  )
}
