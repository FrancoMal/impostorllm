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
        {leaderboard.slice(0, 5).map((entry, index) => (
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
              <span className="text-sm font-medium">
                {entry.display_name}
              </span>
            </div>

            <div className="text-right">
              <div className="font-bold text-yellow-400">
                {entry.score}
              </div>
              <div className="text-xs text-gray-500">
                {entry.games_played} partidas
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats summary */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
          {leaderboard.slice(0, 3).map(entry => (
            <React.Fragment key={entry.model}>
              <div>
                <span style={{ color: entry.color }}>
                  {entry.display_name}
                </span>
              </div>
              <div className="text-right">
                {entry.vote_accuracy}% acierto
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  )
}
