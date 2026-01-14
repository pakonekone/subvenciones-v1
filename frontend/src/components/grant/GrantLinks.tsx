import { Grant } from "@/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExternalLink, Link2 } from "lucide-react"

interface GrantLinksProps {
  grant: Grant
}

export function GrantLinks({ grant }: GrantLinksProps) {
  const hasLinks = grant.html_url || grant.pdf_url || grant.regulatory_base_url ||
                   grant.electronic_office || grant.bdns_code

  if (!hasLinks) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Link2 className="h-4 w-4" />
          Enlaces utiles
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-3">
          {grant.html_url && (
            <Button variant="outline" className="gap-2" asChild>
              <a href={grant.html_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Ver Publicacion Oficial
              </a>
            </Button>
          )}

          {grant.pdf_url && (
            <Button variant="outline" className="gap-2" asChild>
              <a href={grant.pdf_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Ver PDF / Anuncio
              </a>
            </Button>
          )}

          {grant.regulatory_base_url && (
            <Button variant="outline" className="gap-2" asChild>
              <a href={grant.regulatory_base_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Bases Reguladoras
              </a>
            </Button>
          )}

          {grant.electronic_office && (
            <Button variant="outline" className="gap-2" asChild>
              <a href={grant.electronic_office} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
                Sede Electronica
              </a>
            </Button>
          )}

          {grant.bdns_code && (
            <Button variant="outline" className="gap-2" asChild>
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
      </CardContent>
    </Card>
  )
}
