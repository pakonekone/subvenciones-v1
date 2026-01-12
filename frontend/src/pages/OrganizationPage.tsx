import { useState, useEffect } from "react"
import { OrganizationProfile, ProfileOptions } from "@/types"
import { getApiUrl } from "@/config/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Building2, Save, Loader2, CheckCircle2, AlertCircle } from "lucide-react"

export default function OrganizationPage() {
  const [profile, setProfile] = useState<OrganizationProfile | null>(null)
  const [options, setOptions] = useState<ProfileOptions | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    cif: "",
    organization_type: "",
    sectors: [] as string[],
    regions: [] as string[],
    annual_budget: "",
    employee_count: "",
    founding_year: "",
    capabilities: [] as string[],
    description: "",
  })

  // Load profile and options
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load options
      const optionsRes = await fetch(getApiUrl("/api/v1/organization/options"))
      if (optionsRes.ok) {
        const optionsData = await optionsRes.json()
        setOptions(optionsData)
      }

      // Load profile
      const profileRes = await fetch(getApiUrl("/api/v1/organization"), {
        headers: { "X-User-ID": "demo-user" },
      })
      if (profileRes.ok) {
        const profileData = await profileRes.json()
        if (profileData) {
          setProfile(profileData)
          setFormData({
            name: profileData.name || "",
            cif: profileData.cif || "",
            organization_type: profileData.organization_type || "",
            sectors: profileData.sectors || [],
            regions: profileData.regions || [],
            annual_budget: profileData.annual_budget?.toString() || "",
            employee_count: profileData.employee_count?.toString() || "",
            founding_year: profileData.founding_year?.toString() || "",
            capabilities: profileData.capabilities || [],
            description: profileData.description || "",
          })
        }
      }
    } catch (err) {
      setError("Error cargando datos")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      const payload = {
        name: formData.name,
        cif: formData.cif || null,
        organization_type: formData.organization_type || null,
        sectors: formData.sectors,
        regions: formData.regions,
        annual_budget: formData.annual_budget ? parseFloat(formData.annual_budget) : null,
        employee_count: formData.employee_count ? parseInt(formData.employee_count) : null,
        founding_year: formData.founding_year ? parseInt(formData.founding_year) : null,
        capabilities: formData.capabilities,
        description: formData.description || null,
      }

      const res = await fetch(getApiUrl("/api/v1/organization"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": "demo-user",
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) throw new Error("Error guardando perfil")

      const savedProfile = await res.json()
      setProfile(savedProfile)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error guardando")
    } finally {
      setSaving(false)
    }
  }

  const toggleArrayValue = (field: "sectors" | "regions" | "capabilities", value: string) => {
    setFormData(prev => {
      const current = prev[field]
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value]
      return { ...prev, [field]: updated }
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Building2 className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">Mi Organizacion</h1>
        </div>
        <p className="text-muted-foreground">
          Configura el perfil de tu organizacion para recibir analisis de elegibilidad personalizados.
        </p>
      </div>

      {/* Success message */}
      {success && (
        <div className="mb-6 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-green-600" />
          <span className="text-green-800 dark:text-green-200">Perfil guardado correctamente</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-800 dark:text-red-200">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle>Datos basicos</CardTitle>
            <CardDescription>Informacion general de la organizacion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre de la organizacion *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Fundacion Ejemplo"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cif">CIF</Label>
                <Input
                  id="cif"
                  value={formData.cif}
                  onChange={e => setFormData(prev => ({ ...prev, cif: e.target.value }))}
                  placeholder="G12345678"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Tipo de organizacion</Label>
                <Select
                  value={formData.organization_type}
                  onValueChange={value => setFormData(prev => ({ ...prev, organization_type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {options?.organization_types.map(opt => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="founding_year">Ano de fundacion</Label>
                <Input
                  id="founding_year"
                  type="number"
                  min="1900"
                  max={new Date().getFullYear()}
                  value={formData.founding_year}
                  onChange={e => setFormData(prev => ({ ...prev, founding_year: e.target.value }))}
                  placeholder="2010"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="employee_count">Numero de empleados</Label>
                <Input
                  id="employee_count"
                  type="number"
                  min="0"
                  value={formData.employee_count}
                  onChange={e => setFormData(prev => ({ ...prev, employee_count: e.target.value }))}
                  placeholder="12"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="annual_budget">Presupuesto anual (EUR)</Label>
              <Input
                id="annual_budget"
                type="number"
                min="0"
                step="1000"
                value={formData.annual_budget}
                onChange={e => setFormData(prev => ({ ...prev, annual_budget: e.target.value }))}
                placeholder="500000"
              />
            </div>
          </CardContent>
        </Card>

        {/* Sectors */}
        <Card>
          <CardHeader>
            <CardTitle>Sectores de actividad</CardTitle>
            <CardDescription>Selecciona los sectores en los que trabaja tu organizacion</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {options?.sectors.map(sector => (
                <div key={sector.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`sector-${sector.value}`}
                    checked={formData.sectors.includes(sector.value)}
                    onCheckedChange={() => toggleArrayValue("sectors", sector.value)}
                  />
                  <label
                    htmlFor={`sector-${sector.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {sector.label}
                  </label>
                </div>
              ))}
            </div>
            {formData.sectors.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {formData.sectors.map(s => {
                  const label = options?.sectors.find(opt => opt.value === s)?.label || s
                  return (
                    <Badge key={s} variant="secondary">
                      {label}
                    </Badge>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Regions */}
        <Card>
          <CardHeader>
            <CardTitle>Ambito geografico</CardTitle>
            <CardDescription>Regiones donde opera tu organizacion</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {options?.regions.map(region => (
                <div key={region.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`region-${region.value}`}
                    checked={formData.regions.includes(region.value)}
                    onCheckedChange={() => toggleArrayValue("regions", region.value)}
                  />
                  <label
                    htmlFor={`region-${region.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {region.label}
                  </label>
                </div>
              ))}
            </div>
            {formData.regions.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {formData.regions.map(r => {
                  const label = options?.regions.find(opt => opt.value === r)?.label || r
                  return (
                    <Badge key={r} variant="outline">
                      {label}
                    </Badge>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Capabilities */}
        <Card>
          <CardHeader>
            <CardTitle>Capacidades</CardTitle>
            <CardDescription>Que puede hacer tu organizacion (para matching con requisitos)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {options?.capabilities.map(cap => (
                <div key={cap.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`cap-${cap.value}`}
                    checked={formData.capabilities.includes(cap.value)}
                    onCheckedChange={() => toggleArrayValue("capabilities", cap.value)}
                  />
                  <label
                    htmlFor={`cap-${cap.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {cap.label}
                  </label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle>Descripcion / Mision</CardTitle>
            <CardDescription>Describe brevemente que hace tu organizacion</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={formData.description}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Somos una organizacion dedicada a..."
              rows={4}
            />
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={loadData}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving || !formData.name}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Guardando...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Guardar perfil
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Profile Info */}
      {profile && (
        <div className="mt-8 text-sm text-muted-foreground">
          <p>Perfil creado: {profile.created_at ? new Date(profile.created_at).toLocaleDateString("es-ES") : "N/A"}</p>
          {profile.updated_at && (
            <p>Ultima actualizacion: {new Date(profile.updated_at).toLocaleDateString("es-ES")}</p>
          )}
        </div>
      )}
    </div>
  )
}
