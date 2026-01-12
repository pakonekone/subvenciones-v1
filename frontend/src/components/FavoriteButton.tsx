import { useState } from 'react'
import { Heart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FavoriteButtonProps {
  isFavorite: boolean
  onToggle: () => Promise<void>
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

export function FavoriteButton({
  isFavorite,
  onToggle,
  size = 'md',
  showLabel = false,
  className
}: FavoriteButtonProps) {
  const [isAnimating, setIsAnimating] = useState(false)
  const [isPending, setIsPending] = useState(false)

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()

    if (isPending) return

    setIsPending(true)
    setIsAnimating(true)

    try {
      await onToggle()
    } catch (err) {
      console.error('Error toggling favorite:', err)
    } finally {
      setIsPending(false)
      // Keep animation a bit longer for visual feedback
      setTimeout(() => setIsAnimating(false), 300)
    }
  }

  const sizeClasses = {
    sm: 'h-7 w-7',
    md: 'h-9 w-9',
    lg: 'h-11 w-11'
  }

  const iconSizes = {
    sm: 'h-3.5 w-3.5',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }

  if (showLabel) {
    return (
      <Button
        variant={isFavorite ? 'default' : 'outline'}
        size={size === 'lg' ? 'lg' : size === 'sm' ? 'sm' : 'default'}
        onClick={handleClick}
        disabled={isPending}
        className={cn(
          'gap-2 transition-all duration-200',
          isFavorite && 'bg-red-500 hover:bg-red-600 text-white border-red-500',
          isAnimating && 'scale-95',
          className
        )}
      >
        <Heart
          className={cn(
            iconSizes[size],
            'transition-all duration-200',
            isFavorite && 'fill-current',
            isAnimating && 'scale-125'
          )}
        />
        {isFavorite ? 'Guardado' : 'Guardar'}
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleClick}
      disabled={isPending}
      className={cn(
        sizeClasses[size],
        'p-0 transition-all duration-200',
        isFavorite
          ? 'text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950'
          : 'text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950',
        isAnimating && 'scale-110',
        className
      )}
      title={isFavorite ? 'Quitar de favoritos' : 'Añadir a favoritos'}
    >
      <Heart
        className={cn(
          iconSizes[size],
          'transition-all duration-200',
          isFavorite && 'fill-current',
          isAnimating && !isFavorite && 'scale-125'
        )}
      />
    </Button>
  )
}
