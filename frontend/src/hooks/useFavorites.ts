import { useState, useEffect, useCallback } from 'react'
import { getApiUrl } from '@/config/api'

// Generate or retrieve a persistent user ID
const getUserId = (): string => {
  const storageKey = 'subvenciones_user_id'
  let userId = localStorage.getItem(storageKey)

  if (!userId) {
    // Generate a unique ID
    userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
    localStorage.setItem(storageKey, userId)
  }

  return userId
}

interface UseFavoritesReturn {
  favoriteIds: Set<string>
  isLoading: boolean
  error: string | null
  isFavorite: (grantId: string) => boolean
  toggleFavorite: (grantId: string) => Promise<void>
  addFavorite: (grantId: string, notes?: string) => Promise<void>
  removeFavorite: (grantId: string) => Promise<void>
  refreshFavorites: () => Promise<void>
  favoritesCount: number
}

export function useFavorites(): UseFavoritesReturn {
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const userId = getUserId()

  // Fetch favorites from backend
  const refreshFavorites = useCallback(async () => {
    try {
      setError(null)
      const response = await fetch(getApiUrl('/api/v1/favorites/ids'), {
        headers: {
          'X-User-ID': userId
        }
      })

      if (response.ok) {
        const ids: string[] = await response.json()
        setFavoriteIds(new Set(ids))
      } else {
        // If backend fails, try to use local storage as fallback
        const localFavorites = localStorage.getItem('favorites_backup')
        if (localFavorites) {
          setFavoriteIds(new Set(JSON.parse(localFavorites)))
        }
      }
    } catch (err) {
      console.error('Error fetching favorites:', err)
      // Use local storage as fallback
      const localFavorites = localStorage.getItem('favorites_backup')
      if (localFavorites) {
        setFavoriteIds(new Set(JSON.parse(localFavorites)))
      }
      setError('Error loading favorites')
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  // Load favorites on mount
  useEffect(() => {
    refreshFavorites()
  }, [refreshFavorites])

  // Sync to local storage whenever favorites change
  useEffect(() => {
    localStorage.setItem('favorites_backup', JSON.stringify(Array.from(favoriteIds)))
  }, [favoriteIds])

  const isFavorite = useCallback((grantId: string): boolean => {
    return favoriteIds.has(grantId)
  }, [favoriteIds])

  const addFavorite = useCallback(async (grantId: string, notes?: string) => {
    // Optimistic update
    setFavoriteIds(prev => new Set([...prev, grantId]))

    try {
      const url = notes
        ? `${getApiUrl(`/api/v1/favorites/${grantId}`)}?notes=${encodeURIComponent(notes)}`
        : getApiUrl(`/api/v1/favorites/${grantId}`)

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        }
      })

      if (!response.ok) {
        // Revert on failure
        setFavoriteIds(prev => {
          const next = new Set(prev)
          next.delete(grantId)
          return next
        })
        const error = await response.json()
        throw new Error(error.detail || 'Failed to add favorite')
      }
    } catch (err) {
      // Revert on failure
      setFavoriteIds(prev => {
        const next = new Set(prev)
        next.delete(grantId)
        return next
      })
      setError(err instanceof Error ? err.message : 'Error adding favorite')
      throw err
    }
  }, [userId])

  const removeFavorite = useCallback(async (grantId: string) => {
    // Optimistic update
    setFavoriteIds(prev => {
      const next = new Set(prev)
      next.delete(grantId)
      return next
    })

    try {
      const response = await fetch(getApiUrl(`/api/v1/favorites/${grantId}`), {
        method: 'DELETE',
        headers: {
          'X-User-ID': userId
        }
      })

      if (!response.ok) {
        // Revert on failure
        setFavoriteIds(prev => new Set([...prev, grantId]))
        const error = await response.json()
        throw new Error(error.detail || 'Failed to remove favorite')
      }
    } catch (err) {
      // Revert on failure
      setFavoriteIds(prev => new Set([...prev, grantId]))
      setError(err instanceof Error ? err.message : 'Error removing favorite')
      throw err
    }
  }, [userId])

  const toggleFavorite = useCallback(async (grantId: string) => {
    if (favoriteIds.has(grantId)) {
      await removeFavorite(grantId)
    } else {
      await addFavorite(grantId)
    }
  }, [favoriteIds, addFavorite, removeFavorite])

  return {
    favoriteIds,
    isLoading,
    error,
    isFavorite,
    toggleFavorite,
    addFavorite,
    removeFavorite,
    refreshFavorites,
    favoritesCount: favoriteIds.size
  }
}
