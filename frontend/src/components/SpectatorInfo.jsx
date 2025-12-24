import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGame } from '../context/GameContext'

export default function SpectatorInfo() {
  const { state } = useGame()
  const [isRevealed, setIsRevealed] = useState(false)

  const impostor = state.players.find(p => p.id === state.impostorId)

  if (!state.secretWord) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 rounded-xl p-4 border border-purple-500/30 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-purple-300 flex items-center gap-2">
          <span>👁️</span> Vista de Espectador
        </h3>
        <button
          onClick={() => setIsRevealed(!isRevealed)}
          className="text-xs px-3 py-1 rounded-full bg-purple-600/50 hover:bg-purple-600 transition-colors"
        >
          {isRevealed ? 'Ocultar' : 'Revelar'}
        </button>
      </div>

      <AnimatePresence>
        {isRevealed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            {/* Secret Word */}
            <div className="flex items-center gap-3 bg-black/30 rounded-lg p-3">
              <span className="text-2xl">🔑</span>
              <div>
                <div className="text-xs text-gray-400">Palabra Secreta</div>
                <div className="text-xl font-bold text-yellow-400 uppercase tracking-wide">
                  {state.secretWord}
                </div>
              </div>
            </div>

            {/* Impostor */}
            <div className="flex items-center gap-3 bg-black/30 rounded-lg p-3">
              <span className="text-2xl">🎭</span>
              <div className="flex-1">
                <div className="text-xs text-gray-400">Impostor</div>
                <div className="flex items-center gap-2">
                  {impostor && (
                    <>
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center text-xs"
                        style={{ backgroundColor: impostor.color }}
                      >
                        {impostor.display_name.charAt(0).toUpperCase()}
                      </div>
                      <span
                        className="font-bold"
                        style={{ color: impostor.color }}
                      >
                        {impostor.display_name}
                      </span>
                    </>
                  )}
                </div>
              </div>
              {impostor?.is_eliminated && (
                <span className="text-xs bg-red-900/50 text-red-300 px-2 py-1 rounded">
                  Eliminado
                </span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
