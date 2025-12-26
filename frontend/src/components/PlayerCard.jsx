import React from 'react'
import { motion } from 'framer-motion'

// Map Greek letters to their icons
const GREEK_ICONS = {
  'Alfa': '🅰️',
  'Beta': '🅱️',
  'Gamma': 'Γ',
  'Delta': 'Δ',
  'Epsilon': 'Ε',
  'Zeta': 'Ζ',
  'Sigma': 'Σ',
}

// Format model name for display (e.g., "mistral:7b" → "mistral")
const getShortModelName = (model) => {
  if (!model || model === 'human') return null
  return model.split(':')[0]
}

export default function PlayerCard({
  player,
  isActive = false,
  isThinking = false,
  showWord = false,
  position = 0,
}) {
  // Get Greek letter icon or fallback
  const icon = player.is_human ? '👤' : (GREEK_ICONS[player.display_name] || '🤖')
  const modelName = getShortModelName(player.model)

  return (
    <motion.div
      className={`player-card ${isActive ? 'active' : ''} ${player.is_eliminated ? 'eliminated' : ''} ${isThinking ? 'thinking' : ''}`}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: position * 0.1 }}
    >
      {/* Avatar */}
      <div
        className="player-avatar"
        style={{ backgroundColor: player.color }}
      >
        {isThinking ? (
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            🤔
          </motion.span>
        ) : (
          <span>{icon}</span>
        )}
      </div>

      {/* Name */}
      <div className="text-sm font-medium mt-1">
        {player.display_name}
      </div>

      {/* Model name (only for AI players) */}
      {modelName && !player.is_human && (
        <div className="text-xs text-gray-400 mt-0.5">
          {modelName}
        </div>
      )}

      {/* Words said */}
      {player.words_said && player.words_said.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1 justify-center">
          {player.words_said.map((word, i) => (
            <span
              key={i}
              className="word-bubble"
              style={{ backgroundColor: player.color + '40' }}
            >
              {word}
            </span>
          ))}
        </div>
      )}

      {/* Eliminated indicator */}
      {player.is_eliminated && (
        <div className="text-xs text-red-400 mt-1">
          ❌ Eliminado
        </div>
      )}

      {/* Human indicator */}
      {player.is_human && (
        <div className="text-xs text-yellow-400 mt-1">
          ⭐ Tú
        </div>
      )}
    </motion.div>
  )
}
