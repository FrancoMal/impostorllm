import React, { useState, useEffect } from 'react'

const PLAYER_ICONS = {
  'gemma3': '💎',
  'mistral': '🌪️',
  'llama3': '🦙',
  'phi4': 'Φ',
  'qwen3': '🐼',
}

export default function Leaderboard({ data }) {
  const [leaderboard, setLeaderboard] = useState(data || [])

  useEffect(() => {
    if (data) {
      setLeaderboard(data)
      return
    }

    // Fetch leaderboard if not provided
    fetch('/api/leaderboard')
      .then(res => res.json())
      .then(setLeaderboard)
      .catch(console.error)
  }, [data])

  if (leaderboard.length === 0) {
    return null
  }

  return (
    <div className="leaderboard">
      <h3 className="text-lg font-medium mb-3 flex items-center gap-2">
        🏆 Leaderboard
      </h3>

      <div className="space-y-2">
        {leaderboard.map((entry, index) => (
          <div
            key={entry.model}
            className="leaderboard-entry"
          >
            <div className="flex items-center gap-2">
              <span className="text-gray-500 w-4 text-sm">
                {index + 1}.
              </span>
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-sm"
                style={{ backgroundColor: entry.color }}
              >
                {PLAYER_ICONS[entry.display_name] || '🤖'}
              </div>
              <div>
                <div className="text-sm font-medium">
                  {entry.display_name}
                </div>
                <div className="text-xs text-gray-500">
                  {entry.games_played} partidas
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="font-bold text-yellow-400">
                {entry.score}
              </div>
              <div className="flex gap-2 text-xs justify-end">
                <span className="text-red-400" title="Victorias como impostor">
                  🎭 {entry.wins_as_impostor || 0}
                </span>
                <span className="text-green-400" title="Victorias como inocente">
                  😇 {entry.wins_as_innocent || 0}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed stats */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="text-xs text-gray-500 mb-2">Estadísticas detalladas</div>
        <div className="space-y-1.5">
          {leaderboard.map(entry => (
            <div key={entry.model} className="flex justify-between text-xs">
              <span style={{ color: entry.color }}>
                {entry.display_name}
              </span>
              <div className="flex gap-3 text-gray-400">
                <span title="Veces impostor">
                  🎭 {entry.times_impostor || 0}x
                </span>
                <span title="Acierto en votos">
                  🎯 {entry.vote_accuracy || 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
