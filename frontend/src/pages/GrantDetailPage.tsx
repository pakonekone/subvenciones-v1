import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Grant } from "@/types"
import { getApiUrl } from "@/config/api"
import { useFavorites } from "@/hooks/useFavorites"
import { AgentSidebar } from "@/components/agent/AgentSidebar"
import { GrantHeader, GrantInfoGrid, GrantTimeline, GrantLinks, DocumentsList } from "@/components/grant"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Bot, AlertCircle } from "lucide-react"

export default function GrantDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [grant, setGrant] = useState<Grant | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [agentSidebarOpen, setAgentSidebarOpen] = useState(false)
  const [hasOrganizationProfile, setHasOrganizationProfile] = useState(false)

  const { isFavorite, toggleFavorite } = useFavorites()

  // Fetch grant data
  useEffect(() => {
    const fetchGrant = async () => {
      if (!id) return

      setLoading(true)
      setError(null)

      try {
        const response = await fetch(getApiUrl(`/api/v1/grants/${id}`))
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Convocatoria no encontrada")
          }
          throw new Error("Error cargando la convocatoria")
        }
        const data = await response.json()
        setGrant(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido")
      } finally {
        setLoading(false)
      }
    }

    fetchGrant()
  }, [id])

  // Check organization profile
  useEffect(() => {
    const checkProfile = async () => {
      try {
        const res = await fetch(getApiUrl("/api/v1/organization"), {
          headers: { "X-User-ID": "demo-user" },
        })
        if (res.ok) {
          const profile = await res.json()
          setHasOrganizationProfile(profile !== null)
        }
      } catch {
        // Ignore errors
      }
    }
    checkProfile()
  }, [])

  const handleToggleFavorite = async () => {
    if (grant) {
      await toggleFavorite(grant.id)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="flex items-center gap-4 mb-8">
          <Skeleton className="h-10 w-32" />
        </div>
        <Skeleton className="h-12 w-3/4 mb-4" />
        <Skeleton className="h-6 w-1/2 mb-6" />
        <div className="grid grid-cols-2 gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <Button variant="ghost" onClick={() => navigate('/grants')} className="mb-8">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver a lista
        </Button>
        <div className="flex flex-col items-center justify-center py-16">
          <AlertCircle className="h-16 w-16 text-destructive mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button onClick={() => navigate('/grants')}>
            Volver a la lista de convocatorias
          </Button>
        </div>
      </div>
    )
  }

  // No grant found
  if (!grant) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <Button variant="ghost" onClick={() => navigate('/grants')} className="mb-8">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver a lista
        </Button>
        <div className="text-center py-16">
          <p className="text-muted-foreground">No se encontro la convocatoria</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-5xl">
      {/* Navigation header */}
      <div className="flex items-center justify-between mb-8">
        <Button variant="ghost" onClick={() => navigate('/grants')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver a lista
        </Button>
        <Button onClick={() => setAgentSidebarOpen(true)} className="gap-2">
          <Bot className="h-4 w-4" />
          Analista AI
        </Button>
      </div>

      {/* Grant content */}
      <GrantHeader
        grant={grant}
        isFavorite={isFavorite(grant.id)}
        onToggleFavorite={handleToggleFavorite}
      />

      <GrantInfoGrid grant={grant} />

      {/* BDNS Documents */}
      {grant.source === "BDNS" && grant.bdns_documents && grant.bdns_documents.length > 0 && (
        <div className="mt-8">
          <DocumentsList
            grantId={grant.id}
            documents={grant.bdns_documents}
            processed={grant.bdns_documents_processed || false}
            processedAt={grant.bdns_documents_processed_at}
            onProcessed={() => {
              // Refresh grant data after processing
              fetch(getApiUrl(`/api/v1/grants/${id}`))
                .then(res => res.json())
                .then(data => setGrant(data))
                .catch(console.error)
            }}
          />
        </div>
      )}

      <GrantTimeline grant={grant} />

      <GrantLinks grant={grant} />

      {/* Agent Sidebar */}
      <AgentSidebar
        selectedGrant={grant}
        isOpen={agentSidebarOpen}
        onToggle={() => setAgentSidebarOpen(!agentSidebarOpen)}
        hasOrganizationProfile={hasOrganizationProfile}
      />
    </div>
  )
}
