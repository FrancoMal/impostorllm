import React, { createContext, useContext, useReducer, useCallback } from 'react'

const GameContext = createContext(null)

const initialState = {
  gameId: null,
  phase: 'setup',
  mode: 'all_ai',
  players: [],
  currentPlayerIndex: 0,
  currentRound: 1,
  debateDuration: 60,
  debateMessages: [],
  yourWord: null,
  isHuman: false,
  votes: [],
  liveVotes: [], // Votes shown in real-time during voting phase
  eliminatedId: null,
  result: null,
  winner: null,
  secretWord: null,
  impostorId: null,
  impostorName: null,
  impostorGuess: null,
  leaderboard: [],
  thinkingPlayerId: null,
  connected: false,
  lastConfig: null, // Store config for game continuation
}

function gameReducer(state, action) {
  switch (action.type) {
    case 'SET_GAME':
      return {
        ...state,
        gameId: action.payload.id,
        mode: action.payload.mode,
        players: action.payload.players,
        debateDuration: action.payload.debate_duration || 60,
        yourWord: action.payload.your_word,
        phase: action.payload.phase || 'setup',
        secretWord: action.payload.secret_word,
        impostorId: action.payload.impostor_id,
        impostorName: action.payload.impostor_name,
      }

    case 'SET_CONNECTED':
      return { ...state, connected: action.payload }

    case 'PHASE_CHANGE':
      return {
        ...state,
        phase: action.payload.phase,
        currentRound: action.payload.round || state.currentRound,
        debateDuration: action.payload.duration || state.debateDuration,
        liveVotes: action.payload.phase === 'voting' ? [] : state.liveVotes, // Clear votes when voting starts
      }

    case 'PLAYER_TURN':
      return {
        ...state,
        currentPlayerIndex: state.players.findIndex(
          p => p.id === action.payload.player_id
        ),
      }

    case 'AI_THINKING':
      return {
        ...state,
        thinkingPlayerId: action.payload.thinking ? action.payload.player_id : null,
      }

    case 'PLAYER_WORD':
      return {
        ...state,
        players: state.players.map(p =>
          p.id === action.payload.player_id
            ? { ...p, words_said: [...(p.words_said || []), action.payload.word] }
            : p
        ),
      }

    case 'NEW_DEBATE_MESSAGE':
      return {
        ...state,
        debateMessages: [
          ...state.debateMessages,
          {
            player_id: action.payload.player_id,
            player_name: action.payload.player_name,
            message: action.payload.message,
          },
        ],
      }

    case 'PLAYER_VOTED':
      return {
        ...state,
        liveVotes: [
          ...state.liveVotes,
          {
            voter_id: action.payload.voter_id,
            voter_name: action.payload.voter_name,
            voted_for_name: action.payload.voted_for_name,
            justification: action.payload.justification || "",
          }
        ],
      }

    case 'VOTE_RESULT':
      return {
        ...state,
        votes: action.payload.tie ? [] : state.votes,
      }

    case 'ELIMINATION':
      return {
        ...state,
        eliminatedId: action.payload.eliminated_id,
        votes: action.payload.votes || [],
        players: state.players.map(p =>
          p.id === action.payload.eliminated_id
            ? { ...p, is_eliminated: true }
            : p
        ),
      }

    case 'IMPOSTOR_GUESS':
      return {
        ...state,
        impostorGuess: action.payload.guess,
        secretWord: action.payload.secret_word,
      }

    case 'GAME_OVER':
      return {
        ...state,
        phase: 'game_over',
        result: action.payload.result,
        winner: action.payload.winner,
        secretWord: action.payload.secret_word,
        impostorId: action.payload.impostor_id,
        impostorGuess: action.payload.impostor_guess,
        leaderboard: action.payload.leaderboard || [],
      }

    case 'SET_CONFIG':
      return { ...state, lastConfig: action.payload }

    case 'RESET':
      return { ...initialState, lastConfig: state.lastConfig } // Preserve config for continuation

    case 'FULL_RESET':
      return { ...initialState } // Complete reset including config

    default:
      return state
  }
}

export function GameProvider({ children }) {
  const [state, dispatch] = useReducer(gameReducer, initialState)

  const setGame = useCallback((gameData) => {
    dispatch({ type: 'SET_GAME', payload: gameData })
  }, [])

  const handleMessage = useCallback((message) => {
    const { type, data } = message
    switch (type) {
      case 'game_state':
        dispatch({ type: 'SET_GAME', payload: data })
        break
      case 'phase_change':
        dispatch({ type: 'PHASE_CHANGE', payload: data })
        break
      case 'player_turn':
        dispatch({ type: 'PLAYER_TURN', payload: data })
        break
      case 'ai_thinking':
        dispatch({ type: 'AI_THINKING', payload: data })
        break
      case 'player_word':
        dispatch({ type: 'PLAYER_WORD', payload: data })
        break
      case 'new_debate_message':
        dispatch({ type: 'NEW_DEBATE_MESSAGE', payload: data })
        break
      case 'player_voted':
        dispatch({ type: 'PLAYER_VOTED', payload: data })
        break
      case 'vote_result':
        dispatch({ type: 'VOTE_RESULT', payload: data })
        break
      case 'elimination':
        dispatch({ type: 'ELIMINATION', payload: data })
        break
      case 'impostor_guess':
        dispatch({ type: 'IMPOSTOR_GUESS', payload: data })
        break
      case 'game_over':
        dispatch({ type: 'GAME_OVER', payload: data })
        break
    }
  }, [])

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' })
  }, [])

  const fullReset = useCallback(() => {
    dispatch({ type: 'FULL_RESET' })
  }, [])

  const setConfig = useCallback((config) => {
    dispatch({ type: 'SET_CONFIG', payload: config })
  }, [])

  const setConnected = useCallback((connected) => {
    dispatch({ type: 'SET_CONNECTED', payload: connected })
  }, [])

  const value = {
    state,
    setGame,
    handleMessage,
    reset,
    fullReset,
    setConfig,
    setConnected,
  }

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>
}

export function useGame() {
  const context = useContext(GameContext)
  if (!context) {
    throw new Error('useGame must be used within a GameProvider')
  }
  return context
}
