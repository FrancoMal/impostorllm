import React, { useState, useEffect } from 'react'
import { useGame } from '../context/GameContext'

export default function GameSetup() {
  const { setGame, setConfig } = useGame()
  const [mode, setMode] = useState('all_ai')
  const [debateDuration, setDebateDuration] = useState(60)
  const [humanPosition, setHumanPosition] = useState(null)
  const [playerName, setPlayerName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Ollama models from API
  const [ollamaModels, setOllamaModels] = useState([])
  const [loadingModels, setLoadingModels] = useState(true)

  // Greek player templates
  const [greekPlayers, setGreekPlayers] = useState([])

  // Custom players: list of model names (e.g., ["mistral:7b", "gemma3:4b", ...])
  const [customPlayers, setCustomPlayers] = useState([])

  // Auto-repeat state
  const [autoRepeat, setAutoRepeat] = useState(false)

  // Model selector state
  const [showModelSelector, setShowModelSelector] = useState(false)

  // Fetch Ollama models and Greek player templates on mount
  useEffect(() => {
    const fetchData = async () => {
      setLoadingModels(true)
      try {
        // Fetch Ollama models
        const modelsRes = await fetch('/api/ollama/models')
        if (modelsRes.ok) {
          const modelsData = await modelsRes.json()
          setOllamaModels(modelsData.models || [])
        }

        // Fetch Greek player templates
        const playersRes = await fetch('/api/players')
        if (playersRes.ok) {
          const playersData = await playersRes.json()
          setGreekPlayers(playersData.greek_players || [])
        }
      } catch (err) {
        console.error('Error fetching data:', err)
        setError('Error al conectar con el servidor')
      } finally {
        setLoadingModels(false)
      }
    }
    fetchData()
  }, [])

  // Add a player with selected model
  const addPlayer = (model) => {
    if (customPlayers.length >= 7) return
    setCustomPlayers([...customPlayers, model])
    setShowModelSelector(false)
  }

  // Remove a player by index
  const removePlayer = (index) => {
    if (customPlayers.length <= 3) return
    const newPlayers = [...customPlayers]
    newPlayers.splice(index, 1)
    setCustomPlayers(newPlayers)
    // Reset human position if it's invalid
    if (humanPosition !== null && humanPosition >= newPlayers.length) {
      setHumanPosition(null)
    }
  }

  // Toggle human position
  const toggleHumanPosition = (index) => {
    if (mode !== 'human_player') return
    setHumanPosition(humanPosition === index ? null : index)
  }

  const handleCreateGame = async () => {
    if (customPlayers.length < 3) {
      setError('Necesitas al menos 3 jugadores')
      return
    }

    if (mode === 'human_player' && humanPosition === null) {
      setError('Selecciona tu posición haciendo clic en un jugador')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const payload = {
        mode,
        debate_duration: debateDuration,
        human_position: humanPosition ?? 0,
        human_name: playerName.trim() || 'Jugador',
        auto_repeat: autoRepeat,
        custom_players: customPlayers,
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

  // Get the Greek player template for a position
  const getGreekTemplate = (index) => {
    return greekPlayers[index] || { name: `Player ${index + 1}`, color: '#808080', icon: '?' }
  }

  // Format model name for display
  const formatModelName = (model) => {
    // e.g., "mistral:7b" → "mistral (7b)"
    const parts = model.split(':')
    if (parts.length === 2) {
      return `${parts[0]} (${parts[1]})`
    }
    return model
  }

  // Short model name for player display
  const shortModelName = (model) => {
    return model.split(':')[0]
  }

  if (loadingModels) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-400">Cargando modelos de Ollama...</p>
        </div>
      </div>
    )
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
          {/* Mode selection */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Modo de juego
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => {
                  setMode('all_ai')
                  setHumanPosition(null)
                }}
                className={`p-4 rounded-lg border-2 transition-all ${
                  mode === 'all_ai'
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-1">🤖</div>
                <div className="font-medium">Solo IAs</div>
                <div className="text-xs text-gray-400">Espectador</div>
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
                <div className="font-medium">Con humano</div>
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

          {/* Player list */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="text-sm font-medium">
                Jugadores ({customPlayers.length}/7)
              </label>
              {customPlayers.length < 7 && (
                <button
                  onClick={() => setShowModelSelector(true)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                >
                  <span>+</span> Añadir
                </button>
              )}
            </div>

            {/* Player grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 mb-3">
              {customPlayers.map((model, index) => {
                const template = getGreekTemplate(index)
                const isHuman = mode === 'human_player' && humanPosition === index
                return (
                  <div
                    key={index}
                    onClick={() => mode === 'human_player' ? toggleHumanPosition(index) : null}
                    className={`relative p-3 rounded-lg border-2 transition-all cursor-pointer group ${
                      isHuman
                        ? 'border-yellow-400 bg-yellow-500/20'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                    style={{
                      backgroundColor: isHuman ? undefined : `${template.color}20`,
                      borderColor: isHuman ? undefined : `${template.color}60`
                    }}
                  >
                    {/* Remove button */}
                    {customPlayers.length > 3 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          removePlayer(index)
                        }}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 hover:bg-red-600 rounded-full text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                    )}

                    <div className="text-center">
                      <div className="text-xl mb-1">{isHuman ? '👤' : template.icon}</div>
                      <div className="text-xs font-medium">{isHuman ? (playerName || 'Tú') : template.name}</div>
                      <div
                        className="text-xs text-gray-400 truncate mt-0.5"
                        title={model}
                      >
                        {isHuman ? '—' : shortModelName(model)}
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Empty slots */}
              {customPlayers.length < 3 && (
                <div className="p-3 rounded-lg border-2 border-dashed border-gray-600 flex items-center justify-center">
                  <span className="text-gray-500 text-xs">Mín. 3</span>
                </div>
              )}
            </div>

            {mode === 'human_player' && (
              <p className="text-xs text-center text-gray-500">
                {humanPosition === null
                  ? 'Haz clic en un jugador para ocupar su posición'
                  : 'Haz clic de nuevo para deseleccionar'
                }
              </p>
            )}

            {customPlayers.length === 0 && (
              <p className="text-center text-gray-500 py-4">
                Añade jugadores seleccionando modelos de Ollama
              </p>
            )}
          </div>

          {/* Model selector modal */}
          {showModelSelector && (
            <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
              <div className="bg-gray-800 rounded-xl p-4 max-w-md w-full max-h-[70vh] overflow-hidden flex flex-col">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold">Seleccionar modelo</h3>
                  <button
                    onClick={() => setShowModelSelector(false)}
                    className="text-gray-400 hover:text-white text-xl"
                  >
                    ×
                  </button>
                </div>

                <div className="overflow-y-auto flex-1">
                  {ollamaModels.length === 0 ? (
                    <p className="text-center text-gray-400 py-8">
                      No se encontraron modelos en Ollama.
                      <br />
                      <span className="text-sm">Ejecuta `ollama pull mistral` para descargar uno.</span>
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {ollamaModels.map((model) => (
                        <button
                          key={model}
                          onClick={() => addPlayer(model)}
                          className="w-full p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
                        >
                          <div className="font-medium">{formatModelName(model)}</div>
                          <div className="text-xs text-gray-400">{model}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
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
            disabled={isLoading || customPlayers.length < 3}
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
