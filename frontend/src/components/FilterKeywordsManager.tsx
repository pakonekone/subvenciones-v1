import { useState, useEffect } from "react"
import { getApiUrl } from "@/config/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Plus, RefreshCw, Filter, Search } from "lucide-react"

interface FilterKeywordsManagerProps {
  open: boolean
  onClose: () => void
}

interface KeywordsData {
  keywords: string[]
  total: number
  description: string
}

export function FilterKeywordsManager({ open, onClose }: FilterKeywordsManagerProps) {
  const [bdnsKeywords, setBdnsKeywords] = useState<string[]>([])
  const [boeGrantKeywords, setBoeGrantKeywords] = useState<string[]>([])
  const [boeNonprofitKeywords, setBoeNonprofitKeywords] = useState<string[]>([])
  const [boeSections, setBoeSections] = useState<string[]>([])

  const [newKeyword, setNewKeyword] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("bdns")

  // Load filters from API on mount
  useEffect(() => {
    if (open) {
      loadFilters()
    }
  }, [open])

  const loadFilters = async () => {
    setLoading(true)
    try {
      // Load BDNS filters
      const bdnsRes = await fetch(getApiUrl("/api/v1/filters/bdns"))
      const bdnsData: KeywordsData = await bdnsRes.json()
      setBdnsKeywords(bdnsData.keywords || [])

      // Load BOE filters
      const boeRes = await fetch(getApiUrl("/api/v1/filters/boe"))
      const boeData = await boeRes.json()
      setBoeGrantKeywords(boeData.grant_keywords?.keywords || [])
      setBoeNonprofitKeywords(boeData.nonprofit_keywords?.keywords || [])
      setBoeSections(boeData.sections?.sections || [])
    } catch (error) {
      console.error("Error loading filters:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) return

    const keyword = newKeyword.trim().toLowerCase()

    if (activeTab === "bdns") {
      if (!bdnsKeywords.includes(keyword)) {
        setBdnsKeywords([...bdnsKeywords, keyword])
      }
    } else if (activeTab === "boe-grants") {
      if (!boeGrantKeywords.includes(keyword)) {
        setBoeGrantKeywords([...boeGrantKeywords, keyword])
      }
    } else if (activeTab === "boe-nonprofit") {
      if (!boeNonprofitKeywords.includes(keyword)) {
        setBoeNonprofitKeywords([...boeNonprofitKeywords, keyword])
      }
    }

    setNewKeyword("")
  }

  const handleRemoveKeyword = (keyword: string, list: "bdns" | "boe-grants" | "boe-nonprofit") => {
    if (list === "bdns") {
      setBdnsKeywords(bdnsKeywords.filter(k => k !== keyword))
    } else if (list === "boe-grants") {
      setBoeGrantKeywords(boeGrantKeywords.filter(k => k !== keyword))
    } else if (list === "boe-nonprofit") {
      setBoeNonprofitKeywords(boeNonprofitKeywords.filter(k => k !== keyword))
    }
  }

  const handleReset = () => {
    if (confirm("¿Restaurar filtros por defecto? Se perderán los cambios no guardados.")) {
      loadFilters()
    }
  }

  const handleSave = () => {
    // For now, just save to localStorage
    // Future: POST to /api/v1/filters/bdns and /api/v1/filters/boe
    localStorage.setItem("bdns_keywords", JSON.stringify(bdnsKeywords))
    localStorage.setItem("boe_grant_keywords", JSON.stringify(boeGrantKeywords))
    localStorage.setItem("boe_nonprofit_keywords", JSON.stringify(boeNonprofitKeywords))

    alert("✅ Filtros guardados correctamente (localStorage)")
    onClose()
  }

  const filterKeywords = (keywords: string[]) => {
    if (!searchQuery) return keywords
    return keywords.filter(k => k.toLowerCase().includes(searchQuery.toLowerCase()))
  }

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Gestión de Filtros de Captura
          </DialogTitle>
          <DialogDescription>
            Configura las palabras clave utilizadas para identificar y filtrar subvenciones
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="bdns">
              BDNS Nonprofit ({bdnsKeywords.length})
            </TabsTrigger>
            <TabsTrigger value="boe-grants">
              BOE Grants ({boeGrantKeywords.length})
            </TabsTrigger>
            <TabsTrigger value="boe-nonprofit">
              BOE Nonprofit ({boeNonprofitKeywords.length})
            </TabsTrigger>
          </TabsList>

          {/* BDNS Tab */}
          <TabsContent value="bdns" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Keywords Nonprofit - BDNS</CardTitle>
                <CardDescription>
                  Estas palabras se buscan en el título, finalidad y tipos de beneficiarios.
                  Al menos una debe coincidir para capturar la convocatoria.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Search and Add */}
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Buscar keyword..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Añadir nueva keyword..."
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddKeyword()}
                  />
                  <Button onClick={handleAddKeyword} size="icon">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                {/* Keywords List */}
                <div className="flex flex-wrap gap-2 min-h-[200px] max-h-[300px] overflow-y-auto border rounded-lg p-4 bg-muted/20">
                  {filterKeywords(bdnsKeywords).length === 0 ? (
                    <div className="w-full text-center text-sm text-muted-foreground py-8">
                      {searchQuery ? "No se encontraron keywords" : "No hay keywords configuradas"}
                    </div>
                  ) : (
                    filterKeywords(bdnsKeywords).map((keyword) => (
                      <Badge
                        key={keyword}
                        variant="secondary"
                        className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
                      >
                        {keyword}
                        <button
                          onClick={() => handleRemoveKeyword(keyword, "bdns")}
                          className="ml-1 rounded-full hover:bg-destructive hover:text-destructive-foreground p-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* BOE Grants Tab */}
          <TabsContent value="boe-grants" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Keywords Grants - BOE</CardTitle>
                <CardDescription>
                  Palabras clave para identificar documentos relacionados con subvenciones/ayudas en el BOE.
                  Si un documento contiene alguna, se considera relevante.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Buscar keyword..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Añadir nueva keyword..."
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddKeyword()}
                  />
                  <Button onClick={handleAddKeyword} size="icon">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2 min-h-[200px] max-h-[300px] overflow-y-auto border rounded-lg p-4 bg-muted/20">
                  {filterKeywords(boeGrantKeywords).length === 0 ? (
                    <div className="w-full text-center text-sm text-muted-foreground py-8">
                      {searchQuery ? "No se encontraron keywords" : "No hay keywords configuradas"}
                    </div>
                  ) : (
                    filterKeywords(boeGrantKeywords).map((keyword) => (
                      <Badge
                        key={keyword}
                        variant="secondary"
                        className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
                      >
                        {keyword}
                        <button
                          onClick={() => handleRemoveKeyword(keyword, "boe-grants")}
                          className="ml-1 rounded-full hover:bg-destructive hover:text-destructive-foreground p-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>

                {/* BOE Sections */}
                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-semibold mb-3 text-sm">Secciones BOE Escaneadas:</h4>
                  <div className="space-y-2">
                    {boeSections.map((section) => (
                      <div key={section} className="flex items-center gap-2 text-sm">
                        <div className="h-2 w-2 rounded-full bg-green-500"></div>
                        {section}
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* BOE Nonprofit Tab */}
          <TabsContent value="boe-nonprofit" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Keywords Nonprofit - BOE</CardTitle>
                <CardDescription>
                  Keywords para identificar grants específicas para organizaciones sin ánimo de lucro en BOE.
                  NO excluye otros grants, solo marca como nonprofit.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Buscar keyword..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Añadir nueva keyword..."
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddKeyword()}
                  />
                  <Button onClick={handleAddKeyword} size="icon">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2 min-h-[200px] max-h-[300px] overflow-y-auto border rounded-lg p-4 bg-muted/20">
                  {filterKeywords(boeNonprofitKeywords).length === 0 ? (
                    <div className="w-full text-center text-sm text-muted-foreground py-8">
                      {searchQuery ? "No se encontraron keywords" : "No hay keywords configuradas"}
                    </div>
                  ) : (
                    filterKeywords(boeNonprofitKeywords).map((keyword) => (
                      <Badge
                        key={keyword}
                        variant="secondary"
                        className="gap-1 pr-1 cursor-pointer hover:bg-secondary/80"
                      >
                        {keyword}
                        <button
                          onClick={() => handleRemoveKeyword(keyword, "boe-nonprofit")}
                          className="ml-1 rounded-full hover:bg-destructive hover:text-destructive-foreground p-0.5"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Restaurar
          </Button>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            Guardar Cambios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
