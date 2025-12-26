import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useGame } from '../context/GameContext'
import Leaderboard from './Leaderboard'

const AUTO_CONTINUE_SECONDS = 5

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

const getPlayerIcon = (player) => {
  if (player?.is_human) return '👤'
  return GREEK_ICONS[player?.display_name] || '🤖'
}

const getModelName = (player) => {
  if (!player?.model || player.model === 'human') return null
  return player.model.split(':')[0]
}

export default function GameResult({ onNewGame, onContinue }) {
  const { state } = useGame()
  const canContinue = !!state.lastConfig
  const [countdown, setCountdown] = useState(AUTO_CONTINUE_SECONDS)
  const [paused, setPaused] = useState(false)
  const countdownRef = useRef(null)
  const hasStartedRef = useRef(false)

  const impostor = state.players.find(p => p.id === state.impostorId)
  const innocentsWon = state.winner === 'innocents'

  // Auto-continue countdown - always runs if canContinue
  useEffect(() => {
    if (!canContinue || paused) return

    if (countdown <= 0 && !hasStartedRef.current) {
      hasStartedRef.current = true
      onContinue()
      return
    }

    if (countdown > 0) {
      countdownRef.current = setTimeout(() => {
        setCountdown(prev => prev - 1)
      }, 1000)
    }

    return () => clearTimeout(countdownRef.current)
  }, [countdown, canContinue, paused, onContinue])

  const handlePause = () => {
    setPaused(true)
    clearTimeout(countdownRef.current)
  }

  const handleNewGame = () => {
    handlePause()
    onNewGame()
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="result-overlay"
    >
      <div className="bg-gray-800 rounded-2xl p-8 max-w-lg w-full mx-4 text-center">
        {/* Result header */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
          className="text-6xl mb-4"
        >
          {innocentsWon ? '🎉' : '🎭'}
        </motion.div>

        <h2 className={`text-3xl font-bold mb-2 ${innocentsWon ? 'text-green-400' : 'text-red-400'}`}>
          {innocentsWon ? '¡Inocentes Ganan!' : '¡Impostor Gana!'}
        </h2>

        {/* Result explanation */}
        <p className="text-gray-300 mb-6">
          {state.result === 'innocents_win' && (
            'El impostor fue eliminado y no logró adivinar la palabra.'
          )}
          {state.result === 'impostor_wins_guess' && (
            '¡El impostor adivinó la palabra correcta!'
          )}
          {state.result === 'impostor_wins_hidden' && (
            'El impostor no fue descubierto.'
          )}
        </p>

        {/* Game details */}
        <div className="bg-gray-900 rounded-xl p-4 mb-6 text-left">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400">Palabra secreta</div>
              <div className="text-xl font-bold text-yellow-400">
                {state.secretWord}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Impostor</div>
              <div className="flex items-center gap-2">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: impostor?.color }}
                >
                  {getPlayerIcon(impostor)}
                </div>
                <div>
                  <span className="font-medium">{impostor?.display_name}</span>
                  {getModelName(impostor) && (
                    <span className="text-xs text-gray-400 ml-1">({getModelName(impostor)})</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {state.impostorGuess && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="text-sm text-gray-400">Adivinanza del impostor</div>
              <div className={`text-lg font-bold ${
                state.result === 'impostor_wins_guess' ? 'text-green-400' : 'text-red-400'
              }`}>
                "{state.impostorGuess}"
                {state.result === 'impostor_wins_guess' ? ' ✓' : ' ✗'}
              </div>
            </div>
          )}
        </div>

        {/* Players summary */}
        <div className="mb-6">
          <div className="text-sm text-gray-400 mb-2">Palabras dichas:</div>
          <div className="flex flex-wrap justify-center gap-2">
            {state.players.map(player => (
              <div
                key={player.id}
                className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm ${
                  player.id === state.impostorId
                    ? 'bg-red-500/30 border border-red-500'
                    : 'bg-gray-700'
                }`}
              >
                <span style={{ color: player.color }}>
                  {player.display_name}
                  {getModelName(player) && (
                    <span className="text-gray-500 text-xs"> ({getModelName(player)})</span>
                  )}:
                </span>
                <span className="text-gray-300">
                  {player.words_said?.join(', ') || '-'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Leaderboard */}
        {state.leaderboard && state.leaderboard.length > 0 && (
          <div className="mb-6">
            <Leaderboard data={state.leaderboard} />
          </div>
        )}

        {/* Game buttons */}
        <div className="space-y-3">
          {canContinue && (
            <div className="relative">
              <button
                onClick={onContinue}
                className="w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-medium text-lg transition-colors"
              >
                {!paused && countdown > 0 ? (
                  <>🔄 Siguiente partida en {countdown}s...</>
                ) : (
                  <>🔄 Continuar Partida</>
                )}
              </button>
              {!paused && countdown > 0 && (
                <div className="mt-2">
                  <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-green-400"
                      initial={{ width: '100%' }}
                      animate={{ width: '0%' }}
                      transition={{ duration: AUTO_CONTINUE_SECONDS, ease: 'linear' }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          <button
            onClick={handleNewGame}
            className={`w-full py-3 rounded-lg font-medium text-lg transition-colors ${
              canContinue
                ? 'bg-gray-600 hover:bg-gray-700'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            🎮 {canContinue ? 'Nueva Configuración' : 'Nueva Partida'}
          </button>
        </div>
      </div>
    </motion.div>
  )
}
