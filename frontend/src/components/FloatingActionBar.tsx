import { Button } from "@/components/ui/button"
import { Send, Trash2, Download, X } from "lucide-react"

interface FloatingActionBarProps {
    selectedCount: number
    onSendToN8n: () => void
    onDelete: () => void
    onExport: () => void
    onClearSelection: () => void
    sending?: boolean
}

export function FloatingActionBar({
    selectedCount,
    onSendToN8n,
    onDelete,
    onExport,
    onClearSelection,
    sending
}: FloatingActionBarProps) {
    if (selectedCount === 0) return null

    return (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-200">
            <div className="bg-foreground text-background px-4 py-2 rounded-full shadow-xl flex items-center gap-2 sm:gap-4 border border-border/50">
                <div className="flex items-center gap-2 pl-2">
                    <span className="font-medium whitespace-nowrap">{selectedCount} seleccionados</span>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-5 w-5 rounded-full hover:bg-background/20 text-background/80 hover:text-background"
                        onClick={onClearSelection}
                    >
                        <X className="h-3 w-3" />
                    </Button>
                </div>

                <div className="h-6 w-px bg-background/20" />

                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onSendToN8n}
                        disabled={sending}
                        className="hover:bg-background/20 text-background hover:text-background gap-2"
                    >
                        <Send className="h-4 w-4" />
                        <span className="hidden sm:inline">{sending ? "Enviando..." : "Enviar a N8n"}</span>
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onExport}
                        className="hover:bg-background/20 text-background hover:text-background gap-2"
                    >
                        <Download className="h-4 w-4" />
                        <span className="hidden sm:inline">Exportar</span>
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onDelete}
                        className="hover:bg-red-500/20 text-red-300 hover:text-red-200 gap-2"
                    >
                        <Trash2 className="h-4 w-4" />
                        <span className="hidden sm:inline">Eliminar</span>
                    </Button>
                </div>
            </div>
        </div>
    )
}
