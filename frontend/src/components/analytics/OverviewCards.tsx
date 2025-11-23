import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Euro, FileText, Heart, Lock } from "lucide-react"

interface OverviewCardsProps {
    data: {
        total_grants: number
        total_budget: number
        nonprofit_grants: number
        open_grants: number
        sent_to_n8n: number
        avg_confidence: number
    }
}

export function OverviewCards({ data }: OverviewCardsProps) {
    const formatAmount = (amount: number) => {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR',
            maximumFractionDigits: 0,
            notation: "compact"
        }).format(amount)
    }

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('es-ES').format(num)
    }

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Grants</CardTitle>
                    <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(data.total_grants)}</div>
                    <p className="text-xs text-muted-foreground">
                        Convocatorias capturadas
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Presupuesto Total</CardTitle>
                    <Euro className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{formatAmount(data.total_budget)}</div>
                    <p className="text-xs text-muted-foreground">
                        Volumen económico total
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Nonprofit</CardTitle>
                    <Heart className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(data.nonprofit_grants)}</div>
                    <p className="text-xs text-muted-foreground">
                        {((data.nonprofit_grants / data.total_grants) * 100).toFixed(1)}% del total
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Abiertas</CardTitle>
                    <Lock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(data.open_grants)}</div>
                    <p className="text-xs text-muted-foreground">
                        Convocatorias activas
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
