import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Grant } from "@/types"
import { chatWithGrant } from "@/services/api"
import ReactMarkdown from "react-markdown"

interface Message {
    role: "user" | "assistant"
    content: string
}

interface GrantChatProps {
    grant: Grant
}

export function GrantChat({ grant }: GrantChatProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: `Hola, soy tu analista AI. He analizado la convocatoria **${grant.title}**. \n\nPuedes preguntarme sobre requisitos, plazos, cuantías o cualquier duda específica que tengas.`,
        },
    ])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages, isLoading])

    const handleSend = async () => {
        if (!input.trim() || isLoading) return

        const userMessage = input.trim()
        setInput("")
        setError(null)

        // Add user message immediately
        const newMessages = [
            ...messages,
            { role: "user", content: userMessage } as Message,
        ]
        setMessages(newMessages)
        setIsLoading(true)

        try {
            // Prepare history for API (excluding the last user message we just added)
            const history = messages.map(m => ({
                role: m.role,
                content: m.content
            }))

            const response = await chatWithGrant(grant.id, userMessage, history)

            if (response.success && response.response) {
                // Assuming N8n returns { output: "text response" } or similar
                // Adjust based on actual N8n response structure. 
                // For now, we expect a 'text' or 'message' field, or we dump the JSON
                const aiContent = typeof response.response === 'string'
                    ? response.response
                    : (response.response.output || response.response.text || response.response.message || JSON.stringify(response.response))

                setMessages(prev => [
                    ...prev,
                    { role: "assistant", content: aiContent }
                ])
            } else {
                throw new Error("Respuesta inválida del servidor")
            }
        } catch (err: any) {
            console.error("Chat error:", err)
            setError(err.message || "No se pudo conectar con el analista. Por favor, intenta de nuevo.")
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col h-[500px] border rounded-md bg-background">
            <div className="p-4 border-b bg-muted/30 flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                <div>
                    <h3 className="font-semibold text-sm">Analista AI</h3>
                    <p className="text-xs text-muted-foreground">
                        Pregunta sobre esta convocatoria
                    </p>
                </div>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : "flex-row"
                                }`}
                        >
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarFallback className={message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}>
                                    {message.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                </AvatarFallback>
                            </Avatar>

                            <div
                                className={`rounded-lg p-3 max-w-[80%] text-sm ${message.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted"
                                    }`}
                            >
                                {message.role === "assistant" ? (
                                    <div className="prose prose-sm dark:prose-invert max-w-none">
                                        <ReactMarkdown>{message.content}</ReactMarkdown>
                                    </div>
                                ) : (
                                    message.content
                                )}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-3">
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarFallback className="bg-muted">
                                    <Bot className="h-4 w-4" />
                                </AvatarFallback>
                            </Avatar>
                            <div className="bg-muted rounded-lg p-3 flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="text-xs text-muted-foreground">Analizando...</span>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="flex justify-center">
                            <div className="bg-destructive/10 text-destructive text-xs px-3 py-2 rounded-full flex items-center gap-2">
                                <AlertCircle className="h-3 w-3" />
                                {error}
                            </div>
                        </div>
                    )}

                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            <div className="p-4 border-t mt-auto">
                <div className="flex gap-2">
                    <Input
                        placeholder="Escribe tu pregunta..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        className="flex-1"
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        size="icon"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
