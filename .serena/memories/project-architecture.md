# Impostor LLM - Project Architecture

## Overview
A social deduction word game where LLMs compete to identify the impostor. Built with FastAPI + React + Ollama.

## Tech Stack
- **Backend**: Python 3.10+, FastAPI, WebSocket, Pydantic
- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion
- **LLM**: Ollama (local models: gemma3, mistral, llama3, phi4, qwen3)

## Directory Structure
```
impostorllm/
├── backend/
│   ├── main.py              # FastAPI + WebSocket endpoints
│   ├── requirements.txt
│   ├── game/
│   │   ├── logic.py         # GameController (flow orchestration)
│   │   ├── state.py         # GameManager (state mutations)
│   │   ├── prompts.py       # LLM prompt templates
│   │   ├── words.py         # Word categories and selection
│   │   └── players.py       # Player config and defaults
│   ├── models/
│   │   └── schemas.py       # Pydantic models (GameState, Player, etc.)
│   ├── llm/
│   │   ├── ollama_client.py # Ollama API client
│   │   └── players.py       # LLM player definitions
│   └── data/
│       └── words.json       # Word categories
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── GameSetup.jsx      # Game config + player selection
│   │   │   ├── WordReveal.jsx     # Secret word display
│   │   │   ├── WordRound.jsx      # Word submission phase
│   │   │   ├── DebateChat.jsx     # Debate messages
│   │   │   ├── VotingPanel.jsx    # Vote interface + live votes
│   │   │   ├── ImpostorGuess.jsx  # Final guess opportunity
│   │   │   ├── GameResult.jsx     # Winner display
│   │   │   └── Leaderboard.jsx    # Score tracking
│   │   ├── context/
│   │   │   └── GameContext.jsx    # Global game state
│   │   └── hooks/
│   │       └── useWebSocket.js    # WS connection management
│   └── package.json
│
└── README.md
```

## Game Phases
1. **SETUP** → Player selection, mode config
2. **WORD_REVEAL** → Show secret word (or "IMPOSTOR")
3. **WORD_ROUND** → Each player says one related word
4. **DEBATE** → 5 rounds of discussion
5. **VOTING** → Vote for suspected impostor
6. **ELIMINATION** → Reveal and eliminate
7. **IMPOSTOR_GUESS** → If caught, impostor guesses word
8. **GAME_OVER** → Winner announced

## Game Modes
- **all_ai**: 3-6 AI players (spectator mode)
- **human_player**: 2-5 AI + 1 human player

## Key Patterns
- **Conversation Memory**: Each AI player maintains chat history for context
- **Prompt Separation**: Different prompts for innocent vs impostor roles
- **Think Tag Cleaning**: Strips `<think>` tags from model outputs (qwen3, deepseek-r1)
- **WebSocket Events**: Real-time game state sync between backend and frontend

## Common Commands
```bash
# Backend
cd backend && python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Check Ollama models
ollama list
```
