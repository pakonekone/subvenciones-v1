import { useState, useEffect } from "react"
import { getApiUrl } from "@/config/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  Shield,
  Sparkles,
  FileText,
  Building2,
  Scale,
  ArrowRight,
  TrendingUp,
  Heart,
  Eye,
  Bot
} from "lucide-react"

interface Stats {
  total_grants: number
  total_budget: number
  nonprofit_grants: number
  open_grants: number
}

interface LandingPageProps {
  onEnterApp: () => void
}

export default function LandingPage({ onEnterApp }: LandingPageProps) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await fetch(getApiUrl("/api/v1/analytics/overview?days=365"))
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error("Error loading stats:", err)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000000) {
      return `${(amount / 1000000000).toFixed(1)}B`
    }
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(0)}M`
    }
    if (amount >= 1000) {
      return `${(amount / 1000).toFixed(0)}K`
    }
    return amount.toString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]" />
        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <Badge variant="secondary" className="mb-4 px-4 py-1">
              <Heart className="mr-1 h-3 w-3 text-green-600" />
              Especializado en Tercer Sector
            </Badge>
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
              Subvenciones para{" "}
              <span className="text-primary">ONGs y Fundaciones</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-600">
              La plataforma que filtra automáticamente las convocatorias relevantes para
              entidades sin ánimo de lucro. Con IA integrada para analizar cada oportunidad.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button size="lg" onClick={onEnterApp} className="gap-2">
                Explorar Subvenciones
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" onClick={onEnterApp}>
                Ver Dashboard
              </Button>
            </div>
          </div>

          {/* Stats */}
          {!loading && stats && (
            <div className="mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard
                label="Convocatorias"
                value={stats.total_grants.toLocaleString()}
                icon={<FileText className="h-5 w-5" />}
              />
              <StatCard
                label="Presupuesto Total"
                value={`${formatCurrency(stats.total_budget)}€`}
                icon={<TrendingUp className="h-5 w-5" />}
              />
              <StatCard
                label="Para Nonprofits"
                value={stats.nonprofit_grants.toLocaleString()}
                icon={<Heart className="h-5 w-5 text-green-600" />}
                highlight
              />
              <StatCard
                label="Abiertas Ahora"
                value={stats.open_grants.toLocaleString()}
                icon={<Search className="h-5 w-5" />}
              />
            </div>
          )}
        </div>
      </section>

      {/* Sources Section */}
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              3 Fuentes Oficiales Integradas
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Accede a todas las convocatorias desde un solo lugar
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl gap-8 sm:grid-cols-3">
            <SourceCard
              title="BDNS"
              description="Base de Datos Nacional de Subvenciones"
              icon={<Building2 className="h-8 w-8" />}
              color="bg-orange-500"
              features={["Metadatos completos", "Filtro nonprofit automático", "Documentos adjuntos"]}
            />
            <SourceCard
              title="BOE"
              description="Boletín Oficial del Estado"
              icon={<FileText className="h-8 w-8" />}
              color="bg-blue-500"
              features={["Procesamiento de PDFs", "Extracción de texto", "44 keywords de detección"]}
            />
            <SourceCard
              title="PLACSP"
              description="Plataforma de Contratación Pública"
              icon={<Scale className="h-8 w-8" />}
              color="bg-purple-500"
              features={["Licitaciones públicas", "Códigos CPV", "Contratos del sector público"]}
            />
          </div>
        </div>
      </section>

      {/* Differentiators Section */}
      <section className="py-24 bg-slate-50">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Lo que nos hace diferentes
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              A diferencia de buscadores genéricos, estamos especializados en el tercer sector
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<Heart className="h-6 w-6 text-green-600" />}
              title="Filtrado Nonprofit"
              description="11 palabras clave específicas para detectar convocatorias dirigidas a entidades sin ánimo de lucro"
            />
            <FeatureCard
              icon={<Bot className="h-6 w-6 text-blue-600" />}
              title="Chat con IA"
              description="Pregunta lo que quieras sobre cualquier convocatoria y obtén respuestas contextualizadas"
            />
            <FeatureCard
              icon={<Eye className="h-6 w-6 text-purple-600" />}
              title="Transparencia Total"
              description="Puedes ver exactamente qué keywords usamos para filtrar. Sin cajas negras"
            />
            <FeatureCard
              icon={<Shield className="h-6 w-6 text-emerald-600" />}
              title="Confidence Score"
              description="Cada convocatoria tiene un índice de relevancia nonprofit (0-100%) para priorizar"
            />
            <FeatureCard
              icon={<Sparkles className="h-6 w-6 text-amber-600" />}
              title="Integración N8n"
              description="Automatiza flujos: análisis AI, export a Google Sheets, notificaciones"
            />
            <FeatureCard
              icon={<TrendingUp className="h-6 w-6 text-rose-600" />}
              title="Analytics Avanzado"
              description="Dashboard con métricas, tendencias y distribución por presupuesto y región"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-primary">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Empieza a encontrar oportunidades
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-primary-foreground/80">
            Accede a convocatorias filtradas específicamente para tu organización nonprofit
          </p>
          <div className="mt-10">
            <Button
              size="lg"
              variant="secondary"
              onClick={onEnterApp}
              className="gap-2 text-lg px-8 py-6"
            >
              Explorar Subvenciones
              <ArrowRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-12">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-slate-400">
              Sistema de Subvenciones para el Tercer Sector
            </p>
            <div className="flex gap-4">
              <Badge variant="outline" className="text-slate-400 border-slate-700">
                BOE
              </Badge>
              <Badge variant="outline" className="text-slate-400 border-slate-700">
                BDNS
              </Badge>
              <Badge variant="outline" className="text-slate-400 border-slate-700">
                PLACSP
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Sub-components

function StatCard({
  label,
  value,
  icon,
  highlight
}: {
  label: string
  value: string
  icon: React.ReactNode
  highlight?: boolean
}) {
  return (
    <div className={`rounded-xl p-6 text-center ${
      highlight
        ? "bg-green-50 border-2 border-green-200"
        : "bg-white border border-slate-200"
    }`}>
      <div className="flex justify-center mb-2 text-slate-500">
        {icon}
      </div>
      <div className={`text-2xl font-bold ${highlight ? "text-green-700" : "text-slate-900"}`}>
        {value}
      </div>
      <div className="text-sm text-slate-500">{label}</div>
    </div>
  )
}

function SourceCard({
  title,
  description,
  icon,
  color,
  features
}: {
  title: string
  description: string
  icon: React.ReactNode
  color: string
  features: string[]
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className={`absolute top-0 left-0 right-0 h-1 ${color}`} />
      <CardHeader>
        <div className={`inline-flex h-12 w-12 items-center justify-center rounded-lg ${color} text-white mb-4`}>
          {icon}
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {features.map((feature, i) => (
            <li key={i} className="flex items-center text-sm text-slate-600">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-slate-400" />
              {feature}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

function FeatureCard({
  icon,
  title,
  description
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="flex gap-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm border">
        {icon}
      </div>
      <div>
        <h3 className="font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>
    </div>
  )
}
