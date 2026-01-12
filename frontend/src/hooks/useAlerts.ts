import { useState, useEffect, useCallback } from 'react'
import { getApiUrl } from '@/config/api'

// Reuse the same user ID as favorites
const getUserId = (): string => {
  const storageKey = 'subvenciones_user_id'
  let userId = localStorage.getItem(storageKey)

  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
    localStorage.setItem(storageKey, userId)
  }

  return userId
}

export interface Alert {
  id: number
  user_id: string
  name: string
  email: string
  is_active: boolean
  keywords: string | null
  source: string | null
  min_budget: number | null
  max_budget: number | null
  is_nonprofit: boolean | null
  regions: string[] | null
  sectors: string[] | null
  last_triggered_at: string | null
  matches_count: number
  created_at: string
  updated_at: string | null
}

export interface AlertCreate {
  name: string
  email: string
  keywords?: string
  source?: string
  min_budget?: number
  max_budget?: number
  is_nonprofit?: boolean
  regions?: string[]
  sectors?: string[]
}

export interface AlertUpdate {
  name?: string
  email?: string
  keywords?: string
  source?: string
  min_budget?: number
  max_budget?: number
  is_nonprofit?: boolean
  regions?: string[]
  sectors?: string[]
  is_active?: boolean
}

interface UseAlertsReturn {
  alerts: Alert[]
  isLoading: boolean
  error: string | null
  alertsCount: number
  activeAlertsCount: number
  createAlert: (data: AlertCreate) => Promise<Alert>
  updateAlert: (alertId: number, data: AlertUpdate) => Promise<Alert>
  deleteAlert: (alertId: number) => Promise<void>
  toggleAlert: (alertId: number) => Promise<Alert>
  refreshAlerts: () => Promise<void>
}

export function useAlerts(): UseAlertsReturn {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const userId = getUserId()

  // Fetch alerts from backend
  const refreshAlerts = useCallback(async () => {
    try {
      setError(null)
      const response = await fetch(getApiUrl('/api/v1/alerts'), {
        headers: {
          'X-User-ID': userId
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAlerts(data.alerts)
      } else {
        throw new Error('Failed to fetch alerts')
      }
    } catch (err) {
      console.error('Error fetching alerts:', err)
      setError('Error loading alerts')
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  // Load alerts on mount
  useEffect(() => {
    refreshAlerts()
  }, [refreshAlerts])

  const createAlert = useCallback(async (data: AlertCreate): Promise<Alert> => {
    try {
      const response = await fetch(getApiUrl('/api/v1/alerts'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create alert')
      }

      const newAlert = await response.json()
      setAlerts(prev => [newAlert, ...prev])
      return newAlert
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating alert')
      throw err
    }
  }, [userId])

  const updateAlert = useCallback(async (alertId: number, data: AlertUpdate): Promise<Alert> => {
    try {
      const response = await fetch(getApiUrl(`/api/v1/alerts/${alertId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update alert')
      }

      const updatedAlert = await response.json()
      setAlerts(prev => prev.map(a => a.id === alertId ? updatedAlert : a))
      return updatedAlert
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error updating alert')
      throw err
    }
  }, [userId])

  const deleteAlert = useCallback(async (alertId: number): Promise<void> => {
    // Optimistic update
    const previousAlerts = alerts
    setAlerts(prev => prev.filter(a => a.id !== alertId))

    try {
      const response = await fetch(getApiUrl(`/api/v1/alerts/${alertId}`), {
        method: 'DELETE',
        headers: {
          'X-User-ID': userId
        }
      })

      if (!response.ok) {
        // Revert on failure
        setAlerts(previousAlerts)
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to delete alert')
      }
    } catch (err) {
      setAlerts(previousAlerts)
      setError(err instanceof Error ? err.message : 'Error deleting alert')
      throw err
    }
  }, [alerts, userId])

  const toggleAlert = useCallback(async (alertId: number): Promise<Alert> => {
    // Optimistic update
    setAlerts(prev => prev.map(a =>
      a.id === alertId ? { ...a, is_active: !a.is_active } : a
    ))

    try {
      const response = await fetch(getApiUrl(`/api/v1/alerts/${alertId}/toggle`), {
        method: 'POST',
        headers: {
          'X-User-ID': userId
        }
      })

      if (!response.ok) {
        // Revert on failure
        setAlerts(prev => prev.map(a =>
          a.id === alertId ? { ...a, is_active: !a.is_active } : a
        ))
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to toggle alert')
      }

      const updatedAlert = await response.json()
      setAlerts(prev => prev.map(a => a.id === alertId ? updatedAlert : a))
      return updatedAlert
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error toggling alert')
      throw err
    }
  }, [userId])

  return {
    alerts,
    isLoading,
    error,
    alertsCount: alerts.length,
    activeAlertsCount: alerts.filter(a => a.is_active).length,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleAlert,
    refreshAlerts
  }
}
