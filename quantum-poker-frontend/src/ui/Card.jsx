import React from 'react'

const Card = ({ card, faceDown = false, size = 'medium' }) => {
  if (!card) return null

  const sizeClasses = {
    small: 'w-10 h-14 text-xs',
    medium: 'w-16 h-24 text-sm',
    large: 'w-20 h-28 text-base'
  }

  const cornerSize = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  }

  const centerSize = {
    small: 'text-2xl',
    medium: 'text-4xl',
    large: 'text-5xl'
  }

  if (faceDown) {
    return (
      <div className={`${sizeClasses[size]} playing-card face-down flex items-center justify-center`}>
        <div className="text-2xl">🂠</div>
      </div>
    )
  }

  // Parse card string (e.g., "A♠", "K♥", "Q♦", "J♣")
  const suit = card.slice(-1)
  const rank = card.slice(0, -1)

  const suitColors = {
    '♠': 'text-black',
    '♥': 'text-red-600',
    '♦': 'text-red-600',
    '♣': 'text-black'
  }

  const rankColors = {
    '♠': 'text-black',
    '♥': 'text-red-600',
    '♦': 'text-red-600',
    '♣': 'text-black'
  }

  const suitColor = suitColors[suit] || 'text-gray-600'
  const rankColor = rankColors[suit] || 'text-gray-600'

  return (
    <div className={`${sizeClasses[size]} playing-card`}>
      {/* Top-left corner */}
      <div className={`${cornerSize[size]} corner top-left rank ${rankColor}`}>
        {rank}
      </div>
      
      {/* Center suit */}
      <div className={`${centerSize[size]} center-suit suit ${suitColor} font-bold`}>
        {suit}
      </div>
      
      {/* Bottom-right corner (rotated) */}
      <div className={`${cornerSize[size]} corner bottom-right rank ${rankColor}`}>
        {rank}
      </div>
    </div>
  )
}

export default Card
