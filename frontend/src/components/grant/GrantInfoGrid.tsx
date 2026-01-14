import { Grant } from "@/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Euro, Users, Briefcase, MapPin, FileText } from "lucide-react"

interface GrantInfoGridProps {
  grant: Grant
}

export function GrantInfoGrid({ grant }: GrantInfoGridProps) {
  const formatAmount = (amount: number | null) => {
    if (!amount) return "No especificado"
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* Budget Card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Euro className="h-4 w-4" />
            Presupuesto
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-green-600">
            {formatAmount(grant.budget_amount)}
          </p>
        </CardContent>
      </Card>

      {/* Beneficiaries Card */}
      {grant.beneficiary_types && grant.beneficiary_types.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" />
              Beneficiarios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {grant.beneficiary_types.map((type, index) => (
                <Badge key={index} variant="secondary">
                  {type}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sectors Card */}
      {grant.sectors && grant.sectors.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              Sectores
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {grant.sectors.map((sector, index) => (
                <Badge key={index} variant="outline">
                  {sector}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Regions Card */}
      {grant.regions && grant.regions.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Regiones
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {grant.regions.map((region, index) => (
                <Badge key={index} variant="outline">
                  {region}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Purpose Card - Full width */}
      {grant.purpose && (
        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Finalidad
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{grant.purpose}</p>
          </CardContent>
        </Card>
      )}

      {/* PLACSP Specific Info */}
      {grant.source === 'PLACSP' && (
        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Datos de Licitacion
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {grant.placsp_folder_id && (
                <div>
                  <span className="text-xs text-muted-foreground block">Expediente</span>
                  <span className="text-sm font-medium">{grant.placsp_folder_id}</span>
                </div>
              )}
              {grant.contract_type && (
                <div>
                  <span className="text-xs text-muted-foreground block">Tipo Contrato</span>
                  <span className="text-sm font-medium">{grant.contract_type}</span>
                </div>
              )}
            </div>
            {grant.cpv_codes && grant.cpv_codes.length > 0 && (
              <div className="mt-4">
                <span className="text-xs text-muted-foreground block mb-2">Codigos CPV</span>
                <div className="flex flex-wrap gap-1">
                  {grant.cpv_codes.map((code, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {code}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
