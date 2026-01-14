import { useState } from "react"
import { BDNSDocument } from "@/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Loader2, CheckCircle, Clock, AlertCircle } from "lucide-react"

interface DocumentsListProps {
  grantId: string
  documents: BDNSDocument[]
  processed: boolean
  processedAt?: string | null
  onProcessed?: () => void
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return ""
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocumentsList({
  grantId,
  documents,
  processed,
  processedAt,
  onProcessed
}: DocumentsListProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{
    processed_successfully: number
    failed: number
  } | null>(null)

  if (!documents || documents.length === 0) {
    return null
  }

  const handleProcess = async () => {
    setIsProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`/api/v1/grants/${grantId}/documents/process`, {
        method: "POST"
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || "Error procesando documentos")
      }

      const data = await response.json()
      setResult({
        processed_successfully: data.processed_successfully,
        failed: data.failed
      })

      // Notify parent to refresh grant data
      if (onProcessed) {
        onProcessed()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Documentos de la convocatoria ({documents.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            {processed ? (
              <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                <CheckCircle className="h-3 w-3 mr-1" />
                Procesado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50">
                <Clock className="h-3 w-3 mr-1" />
                Pendiente
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Document list */}
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-3 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <FileText className="h-5 w-5 text-red-500 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" title={doc.nombre}>
                    {doc.nombre}
                  </p>
                  {doc.descripcion && (
                    <p className="text-xs text-muted-foreground truncate" title={doc.descripcion}>
                      {doc.descripcion}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {doc.size && (
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(doc.size)}
                  </span>
                )}
                <Button variant="ghost" size="sm" className="gap-1" asChild>
                  <a href={doc.url} target="_blank" rel="noopener noreferrer">
                    <Download className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Process button */}
        {!processed && (
          <div className="pt-2 border-t">
            <Button
              onClick={handleProcess}
              disabled={isProcessing}
              className="w-full"
              variant="default"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Procesando documentos...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Procesar documentos para el agente AI
                </>
              )}
            </Button>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Extrae el contenido de los PDFs para que el agente AI pueda analizarlos
            </p>
          </div>
        )}

        {/* Result message */}
        {result && (
          <div className="p-3 rounded-lg bg-green-50 border border-green-200">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">
                {result.processed_successfully} documento(s) procesado(s)
                {result.failed > 0 && `, ${result.failed} con errores`}
              </span>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* Processed info */}
        {processed && processedAt && (
          <p className="text-xs text-muted-foreground text-center">
            Procesado el {new Date(processedAt).toLocaleDateString("es-ES", {
              day: "numeric",
              month: "long",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit"
            })}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
