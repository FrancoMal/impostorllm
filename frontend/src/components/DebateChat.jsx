import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGame } from '../context/GameContext'

const PLAYER_ICONS = {
  'gemma3': '💎',
  'mistral': '🌪️',
  'llama3': '🦙',
  'phi4': 'Φ',
  'qwen3': '🐼',
}

export default function DebateChat({ onSendMessage }) {
  const { state } = useGame()
  const [message, setMessage] = useState('')
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
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={chatRef}
        className="h-80 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
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
              const icon = player?.is_human ? '👤' : (PLAYER_ICONS[msg.player_name] || '🤖')

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
                    <div className="flex items-center gap-2 mb-2">
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
                      <span className="text-xs text-gray-500">
                        #{index + 1}
                      </span>
                    </div>

                    {/* Message Content */}
                    <p className="text-gray-200 text-sm leading-relaxed pl-10">
                      {msg.message}
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
