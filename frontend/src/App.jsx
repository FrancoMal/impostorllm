import React, { useState, useCallback, useEffect, useRef } from 'react'
import { GameProvider, useGame } from './context/GameContext'
import { useWebSocket } from './hooks/useWebSocket'
import GameSetup from './components/GameSetup'
import GameTable from './components/GameTable'
import DebateChat from './components/DebateChat'
import VotingPanel from './components/VotingPanel'
import ImpostorGuess from './components/ImpostorGuess'
import GameResult from './components/GameResult'
import Leaderboard from './components/Leaderboard'
import Timer from './components/Timer'
import SpectatorInfo from './components/SpectatorInfo'

function GameApp() {
  const { state, handleMessage, setConnected, reset, fullReset, setGame } = useGame()
  const [ws, setWs] = useState(null)

  const onMessage = useCallback((message) => {
    handleMessage(message)
  }, [handleMessage])

  const onConnect = useCallback(() => {
    setConnected(true)
  }, [setConnected])

  const onDisconnect = useCallback(() => {
    setConnected(false)
  }, [setConnected])

  const { isConnected, send, disconnect } = useWebSocket(
    state.gameId,
    onMessage,
    onConnect,
    onDisconnect
  )

  const handleStartGame = useCallback(() => {
    send('start_game')
  }, [send])

  // Auto-start game when in setup phase with auto-repeat enabled
  const autoStartedRef = useRef(false)
  useEffect(() => {
    // Only auto-start if:
    // - We're in setup phase
    // - Connected to WebSocket
    // - Auto-repeat is enabled (lastConfig exists)
    // - Haven't already auto-started this game
    if (
      state.phase === 'setup' &&
      isConnected &&
      state.lastConfig &&
      state.gameId &&
      !autoStartedRef.current
    ) {
      autoStartedRef.current = true
      // Small delay to ensure everything is ready
      setTimeout(() => {
        send('start_game')
      }, 500)
    }

    // Reset auto-start flag when game ends
    if (state.phase === 'game_over') {
      autoStartedRef.current = false
    }
  }, [state.phase, isConnected, state.lastConfig, state.gameId, send])

  const handleSubmitWord = useCallback((word) => {
    send('player_word', { word })
  }, [send])

  const handleSendDebateMessage = useCallback((message) => {
    send('debate_message', { message })
  }, [send])

  const handleVote = useCallback((votedForId) => {
    send('cast_vote', { voted_for: votedForId })
  }, [send])

  const handleImpostorGuess = useCallback((guess) => {
    send('impostor_guess', { guess })
  }, [send])

  const handleNewGame = useCallback(() => {
    disconnect()
    fullReset()  // Full reset clears config too
  }, [disconnect, fullReset])

  const handleContinueGame = useCallback(async () => {
    if (!state.lastConfig) return

    disconnect()
    reset()  // Reset preserves lastConfig

    try {
      const response = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.lastConfig),
      })

      if (!response.ok) {
        throw new Error('Error al crear el juego')
      }

      const data = await response.json()
      setGame({
        id: data.game_id,
        mode: data.mode,
        players: data.players,
        debate_duration: state.lastConfig.debate_duration || 60,
        phase: 'setup',
      })
    } catch (err) {
      console.error('Error continuing game:', err)
      fullReset()  // On error, go back to setup
    }
  }, [disconnect, reset, fullReset, setGame, state.lastConfig])

  const renderPhase = () => {
    switch (state.phase) {
      case 'setup':
        return (
          <div className="space-y-6">
            <GameTable
              onStartGame={handleStartGame}
              showStartButton={true}
            />
          </div>
        )
      case 'word_reveal':
      case 'word_round':
        return (
          <div className="space-y-6">
            <GameTable
              onStartGame={handleStartGame}
              onSubmitWord={handleSubmitWord}
            />
          </div>
        )
      case 'debate':
        return (
          <div className="space-y-6">
            <GameTable />
            <div className="flex justify-center">
              <Timer duration={state.debateDuration} />
            </div>
            <DebateChat onSendMessage={handleSendDebateMessage} />
          </div>
        )
      case 'voting':
        return (
          <div className="space-y-6">
            <GameTable />
            <VotingPanel onVote={handleVote} />
          </div>
        )
      case 'elimination':
        return (
          <div className="space-y-6">
            <GameTable />
            <div className="text-center py-8">
              <div className="inline-flex items-center gap-3 bg-gray-800 px-6 py-4 rounded-xl">
                <div className="flex gap-1">
                  <span className="w-3 h-3 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-3 h-3 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-3 h-3 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
                <span className="text-xl">Procesando votos...</span>
              </div>
            </div>
          </div>
        )
      case 'impostor_guess':
        return (
          <div className="space-y-6">
            <GameTable />
            <ImpostorGuess onGuess={handleImpostorGuess} />
          </div>
        )
      case 'game_over':
        return <GameResult onNewGame={handleNewGame} onContinue={handleContinueGame} />
      default:
        return null
    }
  }

  // If no game, show setup
  if (!state.gameId) {
    return <GameSetup />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-indigo-950 text-white">
      <div className="max-w-5xl mx-auto p-4">
        {/* Header */}
        <header className="text-center mb-6">
          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
            🎭 Impostor LLM
          </h1>
          <div className="flex justify-center items-center gap-3 text-sm">
            <span className="bg-gray-800 px-3 py-1.5 rounded-lg">
              Ronda {state.currentRound}
            </span>
            <span className={`px-3 py-1.5 rounded-lg flex items-center gap-2 ${
              isConnected
                ? 'bg-green-900/50 text-green-300 border border-green-700'
                : 'bg-red-900/50 text-red-300 border border-red-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></span>
              {isConnected ? 'Conectado' : 'Desconectado'}
            </span>
            <span className="bg-blue-900/50 text-blue-300 px-3 py-1.5 rounded-lg border border-blue-700 capitalize">
              {state.phase.replace('_', ' ')}
            </span>
          </div>
        </header>

        {/* Spectator Info - Only show when game is active */}
        {state.phase !== 'setup' && state.phase !== 'game_over' && (
          <div className="mb-6">
            <SpectatorInfo />
          </div>
        )}

        {/* Main content */}
        <main>
          {renderPhase()}
        </main>

        {/* Leaderboard sidebar */}
        {state.phase !== 'setup' && state.phase !== 'game_over' && (
          <aside className="fixed top-4 right-4 w-72 hidden xl:block">
            <Leaderboard />
          </aside>
        )}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <GameProvider>
      <GameApp />
    </GameProvider>
  )
}
