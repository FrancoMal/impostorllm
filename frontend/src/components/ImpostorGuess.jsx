import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useGame } from '../context/GameContext'

export default function ImpostorGuess({ onGuess }) {
  const { state } = useGame()
  const [guess, setGuess] = useState('')
  const [hasGuessed, setHasGuessed] = useState(false)

  const humanPlayer = state.players.find(p => p.is_human)
  const impostor = state.players.find(p => p.is_impostor)
  const isHumanImpostor = humanPlayer && impostor && humanPlayer.id === impostor.id

  // Get all words said during the game
  const allWords = state.players
    .flatMap(p => p.words_said?.map(w => ({ player: p.display_name, word: w })) || [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (guess.trim() && onGuess) {
      onGuess(guess.trim())
      setHasGuessed(true)
    }
  }

  if (!isHumanImpostor) {
    // AI impostor is guessing
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-800 rounded-xl p-6 text-center"
      >
        <h3 className="text-xl font-bold text-red-400 mb-4">
          🎭 El impostor fue descubierto
        </h3>
        <p className="text-gray-300 mb-4">
          El impostor tiene una oportunidad de adivinar la palabra secreta...
        </p>
        <div className="animate-pulse text-yellow-400">
          {impostor?.display_name} está pensando...
        </div>
      </motion.div>
    )
  }

  if (hasGuessed) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-gray-800 rounded-xl p-6 text-center"
      >
        <h3 className="text-xl font-bold mb-4">🤔 Tu adivinanza</h3>
        <p className="text-2xl font-bold text-yellow-400 mb-4">{guess}</p>
        <p className="text-gray-400 animate-pulse">
          Verificando...
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800 rounded-xl p-6"
    >
      <h3 className="text-xl font-bold text-red-400 mb-2 text-center">
        🎭 ¡Te descubrieron!
      </h3>
      <p className="text-gray-300 text-center mb-4">
        Pero tienes una última oportunidad. Si adivinas la palabra secreta, ¡ganas!
      </p>

      {/* Show all words as hints */}
      <div className="bg-gray-900 rounded-lg p-4 mb-4">
        <div className="text-sm text-gray-400 mb-2">Palabras dichas:</div>
        <div className="flex flex-wrap gap-2">
          {allWords.map((item, i) => (
            <span
              key={i}
              className="px-2 py-1 bg-gray-700 rounded text-sm"
            >
              <span className="text-gray-400">{item.player}:</span>{' '}
              <span className="text-white">{item.word}</span>
            </span>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            ¿Cuál crees que era la palabra secreta?
          </label>
          <input
            type="text"
            value={guess}
            onChange={(e) => setGuess(e.target.value)}
            placeholder="Escribe tu adivinanza..."
            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-yellow-500 text-lg"
            autoFocus
          />
        </div>

        <button
          type="submit"
          disabled={!guess.trim()}
          className="w-full py-3 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 rounded-lg font-medium text-lg transition-colors"
        >
          🎯 Adivinar
        </button>
      </form>
    </motion.div>
  )
}
