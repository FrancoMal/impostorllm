import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGame } from '../context/GameContext'

const PLAYER_ICONS = {
  'gemma3': '💎',
  'mistral': '🌪️',
  'llama3': '🦙',
  'phi4': 'Φ',
  'qwen3': '🐼',
}

function LiveVotesDisplay({ liveVotes, players }) {
  if (!liveVotes || liveVotes.length === 0) return null

  const getPlayerInfo = (name) => {
    const player = players?.find(p => p.display_name === name)
    return {
      color: player?.color || '#fff',
      icon: player?.is_human ? '👤' : (PLAYER_ICONS[name] || '🤖')
    }
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-700">
      <h4 className="text-sm font-medium text-gray-400 mb-3">Votos registrados:</h4>
      <div className="space-y-3">
        <AnimatePresence>
          {liveVotes.map((vote, index) => {
            const voter = getPlayerInfo(vote.voter_name)
            const votedFor = getPlayerInfo(vote.voted_for_name)
            return (
              <motion.div
                key={`${vote.voter_id}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="bg-gray-700/50 rounded-lg px-4 py-3"
              >
                {/* Vote header */}
                <div className="flex items-center gap-2 text-sm">
                  <span
                    className="flex items-center gap-1"
                    style={{ color: voter.color }}
                  >
                    {voter.icon}
                    <span className="font-medium">{vote.voter_name}</span>
                  </span>
                  <span className="text-gray-500">vota por</span>
                  <span
                    className="flex items-center gap-1"
                    style={{ color: votedFor.color }}
                  >
                    {votedFor.icon}
                    <span className="font-medium">{vote.voted_for_name}</span>
                  </span>
                </div>
                {/* Justification */}
                {vote.justification && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-2 text-xs text-gray-400 italic border-l-2 border-gray-600 pl-3"
                  >
                    "{vote.justification}"
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default function VotingPanel({ onVote }) {
  const { state } = useGame()
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [hasVoted, setHasVoted] = useState(false)

  const humanPlayer = state.players.find(p => p.is_human)
  const votablePlayers = state.players.filter(
    p => !p.is_eliminated && (!humanPlayer || p.id !== humanPlayer.id)
  )

  const handleVote = () => {
    if (selectedPlayer && onVote) {
      onVote(selectedPlayer)
      setHasVoted(true)
    }
  }

  if (!humanPlayer) {
    // AI-only mode - show voting progress with live votes
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-medium mb-4 text-center">🗳️ Votación</h3>
        <p className="text-gray-400 animate-pulse text-center">
          Las IAs están votando...
        </p>
        <LiveVotesDisplay liveVotes={state.liveVotes} players={state.players} />
      </div>
    )
  }

  if (hasVoted) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-medium mb-4 text-center">🗳️ Votación</h3>
        <p className="text-green-400 text-center">
          ✓ Voto registrado
        </p>
        <p className="text-gray-400 text-sm mt-2 text-center">
          Esperando a que todos voten...
        </p>
        <LiveVotesDisplay liveVotes={state.liveVotes} players={state.players} />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800 rounded-xl p-6"
    >
      <h3 className="text-lg font-medium mb-4 text-center">
        🗳️ ¿Quién es el impostor?
      </h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {votablePlayers.map((player) => (
          <motion.button
            key={player.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelectedPlayer(player.id)}
            className={`vote-button flex items-center gap-3 text-left ${
              selectedPlayer === player.id
                ? 'ring-2 ring-yellow-400 bg-yellow-500/20'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-lg"
              style={{ backgroundColor: player.color }}
            >
              {player.is_human ? '👤' : (PLAYER_ICONS[player.display_name] || '🤖')}
            </div>
            <div>
              <div className="font-medium">({player.display_name})</div>
              <div className="text-xs text-gray-400">
                {player.words_said?.join(', ') || 'Sin palabras'}
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      <button
        onClick={handleVote}
        disabled={!selectedPlayer}
        className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
      >
        {selectedPlayer ? (
          <>🗳️ Votar por ({state.players.find(p => p.id === selectedPlayer)?.display_name})</>
        ) : (
          'Selecciona un jugador'
        )}
      </button>
    </motion.div>
  )
}
