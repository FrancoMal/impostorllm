import React, { useState, useEffect } from 'react'
import { useGame } from '../context/GameContext'

export default function GameSetup() {
  const { setGame, setConfig } = useGame()
  const [mode, setMode] = useState('all_ai')
  const [debateDuration, setDebateDuration] = useState(60)
  const [humanPosition, setHumanPosition] = useState(0)
  const [playerName, setPlayerName] = useState('')  // Custom player name
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Player selection state
  const [availablePlayers, setAvailablePlayers] = useState([])
  const [selectedPlayers, setSelectedPlayers] = useState([])
  const [defaultPlayers, setDefaultPlayers] = useState([])

  // Single-model mode state
  const [singleModelMode, setSingleModelMode] = useState(false)
  const [selectedModel, setSelectedModel] = useState('')
  const [availableModels, setAvailableModels] = useState([])
  const [singleModelNames, setSingleModelNames] = useState([])
  const [playerCount, setPlayerCount] = useState(5)

  // Auto-repeat state
  const [autoRepeat, setAutoRepeat] = useState(false)

  // Fetch available players on mount
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await fetch('/api/players')
        if (response.ok) {
          const data = await response.json()
          setAvailablePlayers(data.players)
          setDefaultPlayers(data.defaults)
          setSelectedPlayers(data.defaults)
          setAvailableModels(data.available_models || [])
          setSingleModelNames(data.single_model_names || [])
          // Default to first model for single-model mode
          if (data.available_models?.length > 0) {
            setSelectedModel(data.available_models[0])
          }
        }
      } catch (err) {
        console.error('Error fetching players:', err)
      }
    }
    fetchPlayers()
  }, [])

  const togglePlayer = (displayName) => {
    setSelectedPlayers(prev => {
      if (prev.includes(displayName)) {
        // Don't allow less than 3 players
        if (prev.length <= 3) return prev
        return prev.filter(p => p !== displayName)
      } else {
        // Don't allow more than 6 players
        if (prev.length >= 6) return prev
        return [...prev, displayName]
      }
    })
  }

  const handleCreateGame = async () => {
    if (!singleModelMode && selectedPlayers.length < 3) {
      setError('Necesitas al menos 3 jugadores')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const payload = {
        mode,
        debate_duration: debateDuration,
        human_position: humanPosition,
        human_name: playerName.trim() || 'Jugador',  // Default name if empty
        auto_repeat: autoRepeat,
      }

      if (singleModelMode) {
        payload.single_model = selectedModel
        payload.player_count = playerCount
      } else {
        payload.selected_players = selectedPlayers
      }

      const response = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error('Error al crear el juego')
      }

      const data = await response.json()

      // Save config for game continuation (only if auto-repeat is enabled)
      if (autoRepeat) {
        setConfig(payload)
      }

      setGame({
        id: data.game_id,
        mode: data.mode,
        players: data.players,
        debate_duration: debateDuration,
        phase: 'setup',
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Get selected player objects for display
  const selectedPlayerObjects = availablePlayers.filter(p =>
    selectedPlayers.includes(p.display_name)
  )

  // Get player display for single-model mode
  const singleModelPlayerDisplay = singleModelNames.slice(0, playerCount)

  // Get model display name
  const getModelDisplayName = (model) => {
    const player = availablePlayers.find(p => p.model === model)
    return player?.display_name || model.split(':')[0]
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🎭 Impostor LLM</h1>
          <p className="text-gray-400">
            Juego de palabras con IAs locales
          </p>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 space-y-6">
          {/* Single Model Toggle */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Tipo de partida
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setSingleModelMode(false)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  !singleModelMode
                    ? 'border-purple-500 bg-purple-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">🎨</div>
                <div className="font-medium">Multi-modelo</div>
                <div className="text-xs text-gray-400">Diferentes IAs</div>
              </button>
              <button
                onClick={() => setSingleModelMode(true)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  singleModelMode
                    ? 'border-purple-500 bg-purple-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">🧪</div>
                <div className="font-medium">Mismo modelo</div>
                <div className="text-xs text-gray-400">Test de calidad</div>
              </button>
            </div>
          </div>

          {/* Mode selection */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Modo de juego
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setMode('all_ai')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  mode === 'all_ai'
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">🤖</div>
                <div className="font-medium">
                  {singleModelMode ? playerCount : selectedPlayers.length} IAs
                </div>
                <div className="text-xs text-gray-400">Solo observar</div>
              </button>
              <button
                onClick={() => setMode('human_player')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  mode === 'human_player'
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">👤</div>
                <div className="font-medium">
                  {singleModelMode ? playerCount - 1 : selectedPlayers.length - 1} IAs + Tú
                </div>
                <div className="text-xs text-gray-400">Participar</div>
              </button>
            </div>
          </div>

          {/* Player name input - only in human mode */}
          {mode === 'human_player' && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Tu nombre
              </label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Escribe tu nombre..."
                className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
                maxLength={15}
              />
            </div>
          )}

          {/* Single-model selection OR Player selection */}
          {singleModelMode ? (
            <div className="space-y-4">
              {/* Model selection */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Modelo a usar
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  {availableModels.map((model) => (
                    <option key={model} value={model}>
                      {getModelDisplayName(model)} ({model})
                    </option>
                  ))}
                </select>
              </div>

              {/* Player count slider */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Número de jugadores: {playerCount}
                </label>
                <input
                  type="range"
                  min="3"
                  max="6"
                  step="1"
                  value={playerCount}
                  onChange={(e) => setPlayerCount(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>3</span>
                  <span>6</span>
                </div>
              </div>

              {/* Preview single-model players */}
              <div>
                <label className="block text-sm font-medium mb-3">
                  Jugadores ({playerCount}x {getModelDisplayName(selectedModel)})
                </label>
                <div className="flex flex-wrap justify-center gap-2">
                  {singleModelPlayerDisplay.map((player, i) => (
                    <div
                      key={player.name}
                      className="flex flex-col items-center"
                      onClick={() => mode === 'human_player' && setHumanPosition(i)}
                    >
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center text-xl cursor-pointer transition-all ${
                          mode === 'human_player' && humanPosition === i
                            ? 'ring-2 ring-yellow-400 bg-yellow-500/30'
                            : ''
                        }`}
                        style={{ backgroundColor: player.color + '40' }}
                      >
                        {mode === 'human_player' && humanPosition === i ? '👤' : player.icon}
                      </div>
                      <span className="text-xs mt-1 text-gray-400">
                        {mode === 'human_player' && humanPosition === i ? 'Tú' : player.name}
                      </span>
                    </div>
                  ))}
                </div>
                {mode === 'human_player' && (
                  <p className="text-xs text-center text-gray-500 mt-2">
                    Haz clic para elegir tu posición
                  </p>
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Player selection */}
              <div>
                <label className="block text-sm font-medium mb-3">
                  Seleccionar jugadores ({selectedPlayers.length}/6)
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {availablePlayers.map((player) => {
                    const isSelected = selectedPlayers.includes(player.display_name)
                    return (
                      <button
                        key={player.display_name}
                        onClick={() => togglePlayer(player.display_name)}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          isSelected
                            ? 'border-green-500 bg-green-500/20'
                            : 'border-gray-600 hover:border-gray-500 opacity-50'
                        }`}
                      >
                        <div className="text-xl mb-1">{player.icon}</div>
                        <div className="text-xs font-medium">{player.display_name}</div>
                      </button>
                    )
                  })}
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Mínimo 3, máximo 6 jugadores
                </p>
              </div>

              {/* Selected players preview */}
              <div>
                <label className="block text-sm font-medium mb-3">
                  Jugadores seleccionados
                </label>
                <div className="flex flex-wrap justify-center gap-2">
                  {selectedPlayerObjects.map((player, i) => (
                    <div
                      key={player.display_name}
                      className="flex flex-col items-center"
                      onClick={() => mode === 'human_player' && setHumanPosition(i)}
                    >
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center text-xl cursor-pointer transition-all ${
                          mode === 'human_player' && humanPosition === i
                            ? 'ring-2 ring-yellow-400 bg-yellow-500/30'
                            : ''
                        }`}
                        style={{ backgroundColor: player.color + '40' }}
                      >
                        {mode === 'human_player' && humanPosition === i ? '👤' : player.icon}
                      </div>
                      <span className="text-xs mt-1 text-gray-400">
                        {mode === 'human_player' && humanPosition === i ? 'Tú' : player.display_name}
                      </span>
                    </div>
                  ))}
                </div>
                {mode === 'human_player' && (
                  <p className="text-xs text-center text-gray-500 mt-2">
                    Haz clic para elegir tu posición
                  </p>
                )}
              </div>
            </>
          )}

          {/* Debate duration slider */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Duración del debate: {debateDuration}s
            </label>
            <input
              type="range"
              min="30"
              max="300"
              step="10"
              value={debateDuration}
              onChange={(e) => setDebateDuration(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>30s</span>
              <span>5 min</span>
            </div>
          </div>

          {/* Auto-repeat toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
            <div>
              <div className="font-medium">Repetir indefinidamente</div>
              <div className="text-xs text-gray-400">
                Las partidas continúan automáticamente
              </div>
            </div>
            <button
              onClick={() => setAutoRepeat(!autoRepeat)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                autoRepeat ? 'bg-green-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                  autoRepeat ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Start button */}
          <button
            onClick={handleCreateGame}
            disabled={isLoading || (!singleModelMode && selectedPlayers.length < 3)}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Creando...
              </span>
            ) : (
              '🎮 Crear Partida'
            )}
          </button>
        </div>

        {/* Instructions */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p className="mb-2">
            <strong>¿Cómo jugar?</strong>
          </p>
          <ul className="text-left list-disc list-inside space-y-1">
            <li>Todos menos 1 conocen la palabra secreta</li>
            <li>1 impostor debe fingir conocerla</li>
            <li>Cada uno dice una palabra relacionada</li>
            <li>Debaten y votan al sospechoso</li>
            <li>¡Si el impostor adivina la palabra, gana!</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
