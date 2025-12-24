import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGame } from '../context/GameContext'
import PlayerCard from './PlayerCard'
import WordReveal from './WordReveal'

export default function GameTable({ onStartGame, onSubmitWord }) {
  const { state } = useGame()
  const [wordInput, setWordInput] = useState('')

  const humanPlayer = state.players.find(p => p.is_human)
  const isHumanTurn = state.phase === 'word_round' &&
    state.players[state.currentPlayerIndex]?.is_human

  const handleSubmitWord = (e) => {
    e.preventDefault()
    if (wordInput.trim() && onSubmitWord) {
      onSubmitWord(wordInput.trim())
      setWordInput('')
    }
  }

  return (
    <div className="game-container">
      {/* Word Reveal Overlay */}
      <AnimatePresence>
        {state.phase === 'word_reveal' && state.yourWord && (
          <WordReveal word={state.yourWord} />
        )}
      </AnimatePresence>

      {/* Game Info Header */}
      <div className="game-info-header">
        {state.phase === 'setup' ? (
          <button
            onClick={onStartGame}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors text-lg"
          >
            ▶ Iniciar Partida
          </button>
        ) : (
          <div className="flex items-center gap-6 bg-gray-800/80 rounded-xl px-6 py-3">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                Ronda {state.currentRound}
              </div>
              <div className="text-sm text-gray-400 capitalize">
                {state.phase.replace('_', ' ')}
              </div>
            </div>
            {humanPlayer && state.yourWord && state.phase !== 'word_reveal' && (
              <div className="border-l border-gray-600 pl-6">
                <div className="text-xs text-gray-400">Tu palabra:</div>
                <div className="font-bold text-yellow-400 text-lg">
                  {state.yourWord}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Players Grid */}
      <div className="players-grid">
        {state.players.map((player, index) => (
          <div key={player.id} className="player-seat">
            <PlayerCard
              player={player}
              isActive={state.currentPlayerIndex === index}
              isThinking={state.thinkingPlayerId === player.id}
              position={index}
            />
          </div>
        ))}
      </div>

      {/* Human word input */}
      {isHumanTurn && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8"
        >
          <form onSubmit={handleSubmitWord} className="max-w-sm mx-auto">
            <label className="block text-center text-sm text-gray-400 mb-2">
              ¡Es tu turno! Di una palabra relacionada:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={wordInput}
                onChange={(e) => setWordInput(e.target.value)}
                placeholder="Escribe una palabra..."
                className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
                autoFocus
              />
              <button
                type="submit"
                disabled={!wordInput.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-medium transition-colors"
              >
                Enviar
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Waiting for AI */}
      {state.phase === 'word_round' && !isHumanTurn && state.thinkingPlayerId && (
        <div className="text-center mt-6 text-gray-400">
          <span className="animate-pulse">
            {state.players.find(p => p.id === state.thinkingPlayerId)?.display_name} está pensando...
          </span>
        </div>
      )}
    </div>
  )
}
