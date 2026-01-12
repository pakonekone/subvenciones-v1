import { Grant } from "@/types"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Bot,
  X,
  ChevronLeft,
  Sparkles,
  Building2,
  Euro,
  Calendar,
  MapPin,
  ExternalLink,
  Send,
  User,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileText,
  Clock,
  HelpCircle,
  FilePlus,
  Mail,
  ListChecks,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useRef, useEffect } from "react"
import { chatWithGrant } from "@/services/api"
import { marked } from "marked"
import { Textarea } from "@/components/ui/textarea"

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
})

interface Message {
  role: "user" | "assistant"
  content: string
}

interface AgentSidebarProps {
  selectedGrant: Grant | null
  isOpen: boolean
  onToggle: () => void
  hasOrganizationProfile: boolean
}

export function AgentSidebar({
  selectedGrant,
  isOpen,
  onToggle,
  hasOrganizationProfile,
}: AgentSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Quick action buttons configuration
  const quickActions = [
    {
      icon: CheckCircle,
      label: "¿Elegibles?",
      prompt: "¿Nuestra organización es elegible para esta convocatoria? Analiza los requisitos y beneficiarios.",
    },
    {
      icon: FileText,
      label: "Documentación",
      prompt: "¿Qué documentación necesitamos preparar para solicitar esta subvención?",
    },
    {
      icon: Clock,
      label: "Plazos",
      prompt: "¿Cuáles son los plazos y fechas clave de esta convocatoria?",
    },
    {
      icon: HelpCircle,
      label: "Resumen",
      prompt: "Explícame esta convocatoria en términos sencillos. ¿De qué trata y qué financia?",
    },
  ]

  // Document generation actions
  const documentActions = [
    {
      icon: FilePlus,
      label: "Memoria Técnica",
      type: "memoria_tecnica" as const,
      description: "Generar borrador completo",
    },
    {
      icon: Mail,
      label: "Carta",
      type: "carta_presentacion" as const,
      description: "Carta de presentación",
    },
    {
      icon: ListChecks,
      label: "Checklist",
      type: "checklist" as const,
      description: "Lista de documentos",
    },
  ]

  const handleGenerateDocument = (documentType: "memoria_tecnica" | "carta_presentacion" | "checklist") => {
    // Document generation prompts - sent to the same AI agent chat
    const documentPrompts: Record<string, string> = {
      memoria_tecnica: "Genera un borrador de Memoria Técnica para esta convocatoria. Incluye: justificación de la necesidad, descripción del proyecto con objetivos, metodología, cronograma, presupuesto desglosado e indicadores de evaluación. Usa los datos de mi organización y adapta el contenido a los requisitos de la convocatoria.",
      carta_presentacion: "Genera una Carta de Presentación formal para solicitar esta subvención. Presenta nuestra organización, explica por qué nos interesa esta convocatoria y cómo se alinea con nuestra misión.",
      checklist: "Genera un checklist de toda la documentación que necesitamos preparar para esta convocatoria. Indica qué documentos tenemos que conseguir, cuáles podemos tener ya, y cómo obtener los que nos falten.",
    }

    sendMessage(documentPrompts[documentType])
  }

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading || !selectedGrant) return

    const userMessage = messageText.trim()
    setInput("")
    setError(null)

    const newMessages: Message[] = [
      ...messages,
      { role: "user", content: userMessage },
    ]
    setMessages(newMessages)
    setIsLoading(true)

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await chatWithGrant(selectedGrant.id, userMessage, history)

      if (response.success && response.response) {
        let aiContent = typeof response.response === "string"
          ? response.response
          : response.response.output ||
            response.response.text ||
            response.response.message ||
            JSON.stringify(response.response)

        // Clean up nested JSON if present
        if (typeof aiContent === "string" && aiContent.startsWith("{")) {
          try {
            const parsed = JSON.parse(aiContent)
            aiContent = parsed.output || aiContent
          } catch {
            // Keep original
          }
        }

        setMessages((prev) => [...prev, { role: "assistant", content: aiContent }])
      } else {
        throw new Error("Respuesta inválida del servidor")
      }
    } catch (err: any) {
      console.error("Chat error:", err)
      setError(err.message || "No se pudo conectar con el analista")
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (prompt: string) => {
    sendMessage(prompt)
  }

  // Reset chat when grant changes
  useEffect(() => {
    if (selectedGrant) {
      setMessages([
        {
          role: "assistant",
          content: `Hola! Soy tu analista de subvenciones. Estoy analizando:\n\n**${selectedGrant.title}**\n\nPuedo ayudarte a:\n- Verificar si tu organización es elegible\n- Explicar los requisitos\n- Identificar la documentación necesaria\n- Calcular plazos y fechas clave\n\n¿Qué te gustaría saber?`,
        },
      ])
      setError(null)
    }
  }, [selectedGrant?.id])

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isLoading])

  const handleSend = () => {
    sendMessage(input)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatAmount = (amount: number | null) => {
    if (!amount) return null
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  }

  return (
    <>
      {/* Toggle button when closed */}
      {!isOpen && (
        <Button
          onClick={onToggle}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-50 rounded-l-xl rounded-r-none h-32 px-3 bg-gradient-to-b from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-2xl border-l border-t border-b border-primary-foreground/20"
          title="Abrir Analista AI"
        >
          <div className="flex flex-col items-center gap-2">
            <Bot className="h-6 w-6" />
            <span className="text-xs font-medium [writing-mode:vertical-lr] rotate-180">
              Analista AI
            </span>
            <ChevronLeft className="h-4 w-4" />
          </div>
        </Button>
      )}

      {/* Sidebar panel */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full bg-background border-l shadow-2xl z-40 transition-all duration-300 flex flex-col",
          isOpen ? "w-[700px] max-w-[90vw]" : "w-0 overflow-hidden"
        )}
      >
        {/* Header */}
        <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-primary/10 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary rounded-xl shadow-sm">
              <Bot className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Analista AI</h3>
              <p className="text-sm text-muted-foreground">
                Asistente inteligente de subvenciones
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onToggle} className="rounded-full">
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Organization warning */}
        {!hasOrganizationProfile && (
          <div className="px-4 py-3 bg-amber-50 dark:bg-amber-950/50 border-b border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-3">
              <Building2 className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Configura tu organización
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                  Para análisis de elegibilidad personalizados
                </p>
                <a
                  href="/organizacion"
                  className="text-xs text-amber-600 hover:text-amber-700 font-medium mt-1 inline-block"
                >
                  Ir a Mi Organización →
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {selectedGrant ? (
            <>
              {/* Grant summary card */}
              <div className="p-4 border-b bg-muted/30 shrink-0">
                <div className="flex items-start gap-3">
                  <Sparkles className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-muted-foreground mb-1">Analizando convocatoria:</p>
                    <p className="font-medium text-sm leading-tight line-clamp-2">
                      {selectedGrant.title}
                    </p>

                    {/* Quick info pills */}
                    <div className="flex flex-wrap gap-2 mt-3">
                      <Badge variant="outline" className="text-xs">
                        {selectedGrant.source}
                      </Badge>
                      {selectedGrant.is_open ? (
                        <Badge className="text-xs bg-green-500 hover:bg-green-600">Abierta</Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">Cerrada</Badge>
                      )}
                      {formatAmount(selectedGrant.budget_amount) && (
                        <Badge variant="outline" className="text-xs gap-1">
                          <Euro className="h-3 w-3" />
                          {formatAmount(selectedGrant.budget_amount)}
                        </Badge>
                      )}
                      {formatDate(selectedGrant.application_end_date) && (
                        <Badge variant="outline" className="text-xs gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(selectedGrant.application_end_date)}
                        </Badge>
                      )}
                    </div>

                    {/* Region badges */}
                    {selectedGrant.regions && selectedGrant.regions.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {selectedGrant.regions.slice(0, 3).map((region, idx) => (
                          <span key={idx} className="text-xs text-muted-foreground flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {region.replace(/^ES\d+ - /, "")}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* External link */}
                    {(selectedGrant.html_url || selectedGrant.regulatory_base_url) && (
                      <a
                        href={selectedGrant.html_url || selectedGrant.regulatory_base_url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline mt-2 inline-flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Ver convocatoria completa
                      </a>
                    )}
                  </div>
                </div>
              </div>

              {/* Chat messages */}
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <div key={index} className="w-full">
                      {message.role === "user" ? (
                        /* User message - right aligned */
                        <div className="flex justify-end gap-2">
                          <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[85%]">
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          </div>
                          <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0">
                            <User className="h-4 w-4" />
                          </div>
                        </div>
                      ) : (
                        /* Assistant message - full width */
                        <div className="flex gap-3 w-full">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/30 flex items-center justify-center shrink-0 mt-1">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                          <div className="bg-muted rounded-2xl rounded-tl-sm px-5 py-4 min-w-0 flex-1 overflow-hidden">
                            <div
                              className="prose prose-sm dark:prose-invert max-w-none prose-headings:font-semibold prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-hr:my-4"
                              dangerouslySetInnerHTML={{ __html: marked.parse(message.content) as string }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex gap-2">
                      <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/30 flex items-center justify-center shrink-0">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                      <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        <span className="text-sm text-muted-foreground">Analizando...</span>
                      </div>
                    </div>
                  )}

                  {error && (
                    <div className="flex justify-center">
                      <div className="bg-destructive/10 text-destructive text-sm px-4 py-2 rounded-full flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        {error}
                      </div>
                    </div>
                  )}

                  <div ref={scrollRef} />
                </div>
              </div>

              {/* Input area */}
              <div className="px-4 pt-4 pb-6 border-t bg-muted/20 shrink-0 space-y-3">
                {/* Quick action buttons */}
                <div className="flex gap-2 flex-wrap">
                  {quickActions.map((action, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => handleQuickAction(action.prompt)}
                      disabled={isLoading}
                      className="gap-1.5 text-xs h-8 rounded-full bg-background hover:bg-primary/10 hover:text-primary hover:border-primary/50 transition-colors"
                    >
                      <action.icon className="h-3.5 w-3.5" />
                      {action.label}
                    </Button>
                  ))}
                </div>

                {/* Document generation buttons */}
                {hasOrganizationProfile && (
                  <div className="flex gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground self-center mr-1">Generar:</span>
                    {documentActions.map((action, idx) => (
                      <Button
                        key={idx}
                        variant="outline"
                        size="sm"
                        onClick={() => handleGenerateDocument(action.type)}
                        disabled={isLoading}
                        className="gap-1.5 text-xs h-8 rounded-full transition-colors bg-green-50 dark:bg-green-950 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900"
                        title={action.description}
                      >
                        <action.icon className="h-3.5 w-3.5" />
                        {action.label}
                      </Button>
                    ))}
                  </div>
                )}

                {/* Text input */}
                <div className="flex gap-2 items-end">
                  <Textarea
                    ref={textareaRef}
                    placeholder="Escribe tu pregunta..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    className="flex-1 min-h-[44px] max-h-[100px] resize-none rounded-xl border-muted-foreground/20 focus:border-primary text-sm"
                    rows={1}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    size="icon"
                    className="h-11 w-11 rounded-xl shrink-0"
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center">
              <div className="p-6 bg-gradient-to-br from-primary/10 to-primary/20 rounded-full mb-6">
                <Bot className="h-12 w-12 text-primary" />
              </div>
              <h4 className="font-semibold text-xl mb-2">Selecciona una convocatoria</h4>
              <p className="text-muted-foreground max-w-xs">
                Haz clic en cualquier convocatoria de la tabla para analizarla con IA y resolver tus dudas.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
