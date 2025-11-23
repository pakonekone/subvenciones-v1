import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface TopDepartmentsProps {
    data: {
        department: string
        count: number
        total_budget: number
        avg_budget: number
    }[]
}

export function TopDepartments({ data }: TopDepartmentsProps) {
    const formatAmount = (amount: number) => {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR',
            maximumFractionDigits: 0,
            notation: "compact"
        }).format(amount)
    }

    return (
        <Card className="col-span-4">
            <CardHeader>
                <CardTitle>Top Organismos Convocantes</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {data.map((dept, idx) => (
                        <div key={idx} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                            <div className="space-y-1 max-w-[60%]">
                                <p className="text-sm font-medium leading-none truncate" title={dept.department}>
                                    {dept.department}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Promedio: {formatAmount(dept.avg_budget)}
                                </p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <p className="text-sm font-bold">{formatAmount(dept.total_budget)}</p>
                                </div>
                                <Badge variant="secondary" className="w-12 justify-center">
                                    {dept.count}
                                </Badge>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
