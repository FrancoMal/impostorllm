import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGame } from '../context/GameContext'

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

// Normalize string: remove accents and convert to lowercase
function normalizeString(str) {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

// Check if character is a word character (letters, numbers, accented chars)
function isWordChar(char) {
  if (!char) return false
  return /[\p{L}\p{N}]/u.test(char)
}

// Function to highlight player names and words in message
function highlightMessage(message, players) {
  if (!message || !players || players.length === 0) {
    return message
  }

  // Collect all terms to highlight: player names and their words
  const highlights = []

  players.forEach(player => {
    // Add player name
    highlights.push({
      term: player.display_name,
      normalizedTerm: normalizeString(player.display_name),
      color: player.color,
      isName: true
    })

    // Add words said by this player
    if (player.words_said && player.words_said.length > 0) {
      player.words_said.forEach(word => {
        highlights.push({
          term: word,
          normalizedTerm: normalizeString(word),
          color: player.color,
          isName: false
        })
      })
    }
  })

  // Sort by length (longer terms first to avoid partial matches)
  highlights.sort((a, b) => b.normalizedTerm.length - a.normalizedTerm.length)

  if (highlights.length === 0) return message

  // Find all matches with their positions
  const normalizedMessage = normalizeString(message)
  const matches = []

  for (const highlight of highlights) {
    const searchTerm = highlight.normalizedTerm
    let startIndex = 0

    while (startIndex < normalizedMessage.length) {
      const foundIndex = normalizedMessage.indexOf(searchTerm, startIndex)
      if (foundIndex === -1) break

      // Check word boundaries (not part of a larger word)
      const charBefore = normalizedMessage[foundIndex - 1]
      const charAfter = normalizedMessage[foundIndex + searchTerm.length]

      const isWordStart = !isWordChar(charBefore)
      const isWordEnd = !isWordChar(charAfter)

      if (isWordStart && isWordEnd) {
        // Check if this position overlaps with an existing match
        const overlaps = matches.some(m =>
          (foundIndex >= m.start && foundIndex < m.end) ||
          (foundIndex + searchTerm.length > m.start && foundIndex + searchTerm.length <= m.end)
        )

        if (!overlaps) {
          matches.push({
            start: foundIndex,
            end: foundIndex + searchTerm.length,
            color: highlight.color
          })
        }
      }

      startIndex = foundIndex + 1
    }
  }

  // Sort matches by position
  matches.sort((a, b) => a.start - b.start)

  // Build result array
  const result = []
  let lastIndex = 0

  // We need to map normalized positions back to original message
  // Since normalization can change string length (é -> e removes combining char)
  // We'll build a position map
  const posMap = [] // posMap[normalizedIndex] = originalIndex
  let normalizedIdx = 0
  for (let i = 0; i < message.length; i++) {
    const char = message[i]
    const normalizedChar = normalizeString(char)
    for (let j = 0; j < normalizedChar.length; j++) {
      posMap[normalizedIdx + j] = i
    }
    normalizedIdx += normalizedChar.length
  }
  posMap[normalizedIdx] = message.length // End position

  for (const match of matches) {
    const origStart = posMap[match.start]
    const origEnd = posMap[match.end] !== undefined ? posMap[match.end] : message.length

    // Add text before match
    if (origStart > lastIndex) {
      result.push(message.slice(lastIndex, origStart))
    }

    // Add highlighted match
    result.push(
      <span
        key={`match-${match.start}`}
        className="font-bold"
        style={{ color: match.color }}
      >
        {message.slice(origStart, origEnd)}
      </span>
    )

    lastIndex = origEnd
  }

  // Add remaining text
  if (lastIndex < message.length) {
    result.push(message.slice(lastIndex))
  }

  return result.length > 0 ? result : message
}

export default function DebateChat({ onSendMessage }) {
  const { state } = useGame()
  const [message, setMessage] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const chatRef = useRef(null)

  const humanPlayer = state.players.find(p => p.is_human)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [state.debateMessages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && onSendMessage) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  return (
    <div className="bg-gradient-to-b from-gray-800 to-gray-900 rounded-xl overflow-hidden shadow-2xl border border-gray-700">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">💬</span>
          <span>Debate</span>
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded-full">
            {state.debateMessages.length} mensajes
          </span>
          {state.debateRound && (
            <span className="text-xs text-blue-400 bg-blue-900/30 px-2 py-1 rounded-full">
              Ronda {state.debateRound}/5
            </span>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-gray-400 hover:text-white bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded-full transition-colors"
          >
            {isExpanded ? '🔽 Colapsar' : '🔼 Expandir'}
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={chatRef}
        className={`${isExpanded ? 'max-h-[70vh]' : 'h-80'} overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 transition-all duration-300`}
      >
        <AnimatePresence initial={false}>
          {state.debateMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <span className="text-4xl mb-2">🎭</span>
              <p>El debate está por comenzar...</p>
              <p className="text-xs mt-1">Los jugadores discutirán quién es el impostor</p>
            </div>
          ) : (
            state.debateMessages.map((msg, index) => {
              // Find player by name to get their properties
              const player = state.players.find(p => p.display_name === msg.player_name)
              const color = player?.color || '#888'
              const icon = player?.is_human ? '👤' : (GREEK_ICONS[msg.player_name] || '🤖')
              const modelName = player?.model && player.model !== 'human' ? player.model.split(':')[0] : null

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3 }}
                  className="group"
                >
                  <div
                    className="rounded-xl p-3 transition-all duration-200 hover:shadow-lg"
                    style={{
                      background: `linear-gradient(135deg, ${color}15 0%, ${color}08 100%)`,
                      borderLeft: `4px solid ${color}`,
                    }}
                  >
                    {/* Player Header */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm shadow-md"
                        style={{ backgroundColor: color }}
                      >
                        {icon}
                      </div>
                      <span
                        className="font-bold text-sm"
                        style={{ color: color }}
                      >
                        {msg.player_name}
                      </span>
                      {modelName && (
                        <span className="text-xs text-gray-500">
                          ({modelName})
                        </span>
                      )}
                      <span className="text-xs text-gray-600">
                        #{index + 1}
                      </span>
                      {/* Impostor/Inocente label */}
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                        player?.id === state.impostorId
                          ? 'bg-red-900/50 text-red-400'
                          : 'bg-green-900/50 text-green-400'
                      }`}>
                        {player?.id === state.impostorId ? '🎭 Impostor' : '✓ Inocente'}
                      </span>
                      {/* Words said */}
                      {player?.words_said && player.words_said.length > 0 && (
                        <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-0.5 rounded">
                          💬 {player.words_said.join(', ')}
                        </span>
                      )}
                    </div>

                    {/* Message Content */}
                    <p className="text-gray-200 text-sm leading-relaxed pl-10">
                      {highlightMessage(msg.message, state.players)}
                    </p>
                  </div>
                </motion.div>
              )
            })
          )}
        </AnimatePresence>

        {/* Thinking indicator */}
        {state.thinkingPlayerId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3 text-gray-400 text-sm py-2 px-3 bg-gray-800/50 rounded-lg"
          >
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <span>
              {state.players.find(p => p.id === state.thinkingPlayerId)?.display_name} está pensando...
            </span>
          </motion.div>
        )}
      </div>

      {/* Human input */}
      {humanPlayer && (
        <form onSubmit={handleSubmit} className="p-4 bg-gray-800 border-t border-gray-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Escribe tu argumento..."
              className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm transition-all"
            />
            <button
              type="submit"
              disabled={!message.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-xl text-sm font-medium transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/20"
            >
              Enviar
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
