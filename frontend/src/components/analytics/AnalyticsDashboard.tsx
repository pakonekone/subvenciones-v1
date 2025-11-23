import { useState, useEffect } from "react"
import { getApiUrl } from "@/config/api"
import { Button } from "@/components/ui/button"

import { OverviewCards } from "./OverviewCards"
import { TimelineChart } from "./TimelineChart"
import { DistributionCharts } from "./DistributionCharts"
import { TopDepartments } from "./TopDepartments"
import { RefreshCw } from "lucide-react"

interface AnalyticsData {
    total_grants: number
    total_budget: number
    nonprofit_grants: number
    open_grants: number
    sent_to_n8n: number
    avg_confidence: number
    grants_by_source: {
        source: string
        count: number
        total_budget: number
        nonprofit_count: number
        open_count: number
        sent_to_n8n_count: number
    }[]
    grants_by_date: {
        date: string
        count: number
        total_budget: number
    }[]
    budget_distribution: {
        range: string
        count: number
        total_budget: number
    }[]
    top_departments: {
        department: string
        count: number
        total_budget: number
        avg_budget: number
    }[]
}

export default function AnalyticsDashboard() {
    const [data, setData] = useState<AnalyticsData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [days, setDays] = useState(30)

    useEffect(() => {
        loadAnalytics()
    }, [days])

    const loadAnalytics = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await fetch(getApiUrl(`/api/v1/analytics/overview?days=${days}`))
            if (!response.ok) throw new Error('Error cargando analytics')
            const result = await response.json()
            setData(result)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error desconocido')
        } finally {
            setLoading(false)
        }
    }

    if (loading && !data) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                    <p className="text-muted-foreground">Cargando datos...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex h-[50vh] items-center justify-center text-destructive">
                <p>⚠️ {error}</p>
            </div>
        )
    }

    if (!data) return null

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <div className="flex items-center space-x-2">
                    <div className="flex items-center bg-muted rounded-lg p-1">
                        {[7, 30, 90, 365].map((d) => (
                            <Button
                                key={d}
                                variant={days === d ? "secondary" : "ghost"}
                                size="sm"
                                onClick={() => setDays(d)}
                                className="h-8"
                            >
                                {d === 365 ? "1 Año" : `${d} Días`}
                            </Button>
                        ))}
                    </div>
                    <Button size="icon" variant="outline" onClick={loadAnalytics}>
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            <div className="space-y-4">
                <OverviewCards data={data} />

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                    <TimelineChart data={data.grants_by_date} />
                    <div className="col-span-3">
                        {/* Placeholder for future widget or just empty for now, 
                 actually TopDepartments fits better here in a 2-col layout with Timeline? 
                 Let's put TopDepartments below for now or next to Timeline if space permits.
                 Timeline is wide (col-span-4). Let's put TopDepartments next to it (col-span-3).
             */}
                        <TopDepartments data={data.top_departments} />
                    </div>
                </div>

                <DistributionCharts
                    budgetData={data.budget_distribution}
                    sourceData={data.grants_by_source}
                />
            </div>
        </div>
    )
}
