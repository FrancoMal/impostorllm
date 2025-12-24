import React from 'react'
import { motion } from 'framer-motion'
import { useGame } from '../context/GameContext'
import Leaderboard from './Leaderboard'

const PLAYER_ICONS = {
  'gemma3': '💎',
  'mistral': '🌪️',
  'llama3': '🦙',
  'phi4': 'Φ',
  'qwen3': '🐼',
  'Tu': '👤',
}

export default function GameResult({ onNewGame }) {
  const { state } = useGame()

  const impostor = state.players.find(p => p.id === state.impostorId)
  const innocentsWon = state.winner === 'innocents'

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
                  {PLAYER_ICONS[impostor?.display_name] || '🤖'}
                </div>
                <span className="font-medium">({impostor?.display_name})</span>
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
                  {player.display_name}:
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

        {/* New game button */}
        <button
          onClick={onNewGame}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium text-lg transition-colors"
        >
          🎮 Nueva Partida
        </button>
      </div>
    </motion.div>
  )
}
