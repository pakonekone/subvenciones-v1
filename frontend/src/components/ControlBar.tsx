import { Search, LayoutGrid, List, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DateRangePicker, DateRange } from "@/components/DateRangePicker"
import { Badge } from "@/components/ui/badge"
import { QuickFilter } from "@/components/QuickFilters"

interface ControlBarProps {
    // Search
    searchValue: string
    onSearchChange: (value: string) => void

    // Tabs
    activeTab: string
    onTabChange: (value: string) => void

    // Quick Filters
    quickFilters: QuickFilter[]
    onToggleQuickFilter: (id: string) => void

    // Date Filter
    dateRange: DateRange
    onDateRangeChange: (range: DateRange) => void
    dateField: string
    onDateFieldChange: (field: string) => void

    // View Mode
    viewMode: "table" | "cards"
    onViewModeChange: (mode: "table" | "cards") => void

    // Advanced Filters
    onToggleAdvancedFilters: () => void
    hasActiveAdvancedFilters: boolean
}

export function ControlBar({
    searchValue,
    onSearchChange,
    activeTab,
    onTabChange,
    quickFilters,
    onToggleQuickFilter,
    dateRange,
    onDateRangeChange,
    dateField,
    onDateFieldChange,
    viewMode,
    onViewModeChange,
    onToggleAdvancedFilters,
    hasActiveAdvancedFilters
}: ControlBarProps) {
    return (
        <div className="bg-card border rounded-lg p-4 mb-6 space-y-4 shadow-sm">
            <div className="flex flex-col md:flex-row gap-4 items-start justify-between flex-wrap">
                {/* Left Section: Search & Tabs */}
                <div className="flex flex-col sm:flex-row gap-4 flex-1 w-full md:w-auto items-center flex-wrap">
                    <div className="relative max-w-xs w-full min-w-[200px]">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Buscar subvenciones..."
                            className="pl-8 h-9"
                            value={searchValue}
                            onChange={(e) => onSearchChange(e.target.value)}
                        />
                    </div>

                    <Tabs value={activeTab} onValueChange={onTabChange} className="w-full sm:w-auto">
                        <TabsList className="h-9">
                            <TabsTrigger value="all">Todas</TabsTrigger>
                            <TabsTrigger value="open">Abiertas</TabsTrigger>
                            <TabsTrigger value="n8n">Enviadas N8n</TabsTrigger>
                        </TabsList>
                    </Tabs>

                    <div className="h-6 w-px bg-border hidden sm:block" />

                    {/* Quick Filters Chips */}
                    <div className="flex gap-2 flex-wrap pb-2 sm:pb-0 w-full sm:w-auto">
                        {quickFilters.map(filter => (
                            <Badge
                                key={filter.id}
                                variant={filter.active ? "default" : "outline"}
                                className="cursor-pointer hover:bg-primary/90 transition-colors whitespace-nowrap"
                                onClick={() => onToggleQuickFilter(filter.id)}
                            >
                                {filter.label}
                            </Badge>
                        ))}
                    </div>
                </div>

                {/* Right Section: Date & View Controls */}
                <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
                    <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-md">
                        <Select value={dateField} onValueChange={onDateFieldChange}>
                            <SelectTrigger className="h-9 w-[140px] border-0 bg-transparent focus:ring-0">
                                <SelectValue placeholder="Fecha" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="application_end_date">Fecha Límite</SelectItem>
                                <SelectItem value="publication_date">Publicación</SelectItem>
                                <SelectItem value="captured_at">Captura</SelectItem>
                            </SelectContent>
                        </Select>
                        <div className="h-4 w-px bg-border" />
                        <DateRangePicker
                            value={dateRange}
                            onChange={onDateRangeChange}
                            onClear={() => onDateRangeChange({ from: null, to: null })}
                            className="h-9"
                        />
                    </div>

                    <div className="flex items-center gap-1 border rounded-lg p-1 ml-2">
                        <Button
                            variant={viewMode === "table" ? "secondary" : "ghost"}
                            size="sm"
                            onClick={() => onViewModeChange("table")}
                            className="h-9 w-9 p-0"
                        >
                            <List className="h-4 w-4" />
                        </Button>
                        <Button
                            variant={viewMode === "cards" ? "secondary" : "ghost"}
                            size="sm"
                            onClick={() => onViewModeChange("cards")}
                            className="h-9 w-9 p-0"
                        >
                            <LayoutGrid className="h-4 w-4" />
                        </Button>
                    </div>

                    <Button
                        variant={hasActiveAdvancedFilters ? "secondary" : "outline"}
                        size="sm"
                        onClick={onToggleAdvancedFilters}
                        className="h-9 gap-2"
                    >
                        <Filter className="h-4 w-4" />
                        <span className="hidden sm:inline">Filtros</span>
                        {hasActiveAdvancedFilters && (
                            <span className="h-2 w-2 rounded-full bg-primary absolute top-2 right-2" />
                        )}
                    </Button>
                </div>
            </div>
        </div>
    )
}
