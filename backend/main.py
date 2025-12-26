"""
FastAPI server for the Impostor Word Game
v1.1 - Single-model mode support
"""
import asyncio
import json
from typing import Optional
from contextlib import asynccontextmanager

import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from models.schemas import GameConfig, GameMode, WSMessageType
from game.state import game_manager
# Game controller options:
# - logic.py: Sistema original (stateless, reconstruye contexto cada vez)
# - logic2.py: Sistema nuevo (chat persistente por jugador)
from game.logic import GameController
from game.export import generate_game_html
from llm.ollama_client import call_llm, ollama_client
from llm.players import LLM_PLAYERS, DEFAULT_PLAYERS


# Store active WebSocket connections per game
active_connections: dict[str, list[WebSocket]] = {}
# Store active game controllers
game_controllers: dict[str, GameController] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("[INFO] Impostor LLM Game Server starting...")

    # Check Ollama availability
    if await ollama_client.is_available():
        models = await ollama_client.list_models()
        print(f"[OK] Ollama available with models: {', '.join(models[:5])}")
    else:
        print("[WARN] Ollama not available - AI players won't work")

    yield

    # Shutdown
    print("[INFO] Server shutting down...")


app = FastAPI(
    title="Impostor LLM Game",
    description="A word impostor game played by LLMs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST Endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    ollama_available = await ollama_client.is_available()
    return {
        "status": "healthy",
        "ollama": ollama_available
    }


@app.get("/api/test-sigma")
async def test_sigma():
    """Test endpoint to verify server is running new code."""
    return {"last_player": "Sigma", "message": "If you see this, server has new code"}


@app.get("/api/players")
async def get_available_players():
    """Get all available LLM players for selection."""
    # Hardcode Greek players to avoid any caching issues
    GREEK_PLAYERS_DIRECT = [
        {"name": "Alfa", "color": "#FF6B6B", "icon": "🅰️"},
        {"name": "Beta", "color": "#4ECDC4", "icon": "🅱️"},
        {"name": "Gamma", "color": "#45B7D1", "icon": "Γ"},
        {"name": "Delta", "color": "#96CEB4", "icon": "Δ"},
        {"name": "Epsilon", "color": "#DDA0DD", "icon": "Ε"},
        {"name": "Zeta", "color": "#FFA500", "icon": "Ζ"},
        {"name": "Sigma", "color": "#FF69B4", "icon": "Σ"},
    ]
    return {
        "players": [
            {
                "model": p.model,
                "display_name": p.display_name,
                "color": p.color,
                "icon": p.icon
            }
            for p in LLM_PLAYERS
        ],
        "defaults": DEFAULT_PLAYERS,
        "single_model_names": GREEK_PLAYERS_DIRECT,  # For single-model mode
        "available_models": [p.model for p in LLM_PLAYERS],  # Models for single-model selection
        "greek_players": GREEK_PLAYERS_DIRECT  # Greek letter names with colors/icons
    }


@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get list of models installed in Ollama."""
    models = await ollama_client.list_models()
    return {
        "models": models,
        "available": len(models) > 0
    }


@app.post("/api/games")
async def create_game(config: GameConfig):
    """Create a new game."""
    game = game_manager.create_game(config)
    return {
        "game_id": game.id,
        "mode": game.mode.value,
        "players": [
            {
                "id": p.id,
                "display_name": p.display_name,
                "model": p.model,
                "color": p.color,
                "is_human": p.is_human
            }
            for p in game.players
        ]
    }


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """Get game state."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return {
        "id": game.id,
        "phase": game.phase.value,
        "mode": game.mode.value,
        "current_round": game.current_round,
        "debate_duration": game.debate_duration,
        "players": [
            {
                "id": p.id,
                "display_name": p.display_name,
                "model": p.model,
                "color": p.color,
                "is_human": p.is_human,
                "is_eliminated": p.is_eliminated,
                "words_said": p.words_said,
                "score": p.score
            }
            for p in game.players
        ],
        "debate_messages": [
            {
                "player_id": m.player_id,
                "player_name": m.player_name,
                "message": m.message
            }
            for m in game.debate_messages
        ]
    }


@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get the leaderboard."""
    return game_manager.get_leaderboard()


@app.get("/api/games/{game_id}/export", response_class=HTMLResponse)
async def export_game(game_id: str):
    """Export a game as an HTML report."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get leaderboard for the report
    leaderboard = game_manager.get_leaderboard()

    # Generate HTML
    html = generate_game_html(game, leaderboard)

    return HTMLResponse(content=html)


# Directory for auto-saved exports
EXPORTS_DIR = Path(__file__).parent / "exports"


@app.post("/api/games/{game_id}/autosave")
async def autosave_game(game_id: str):
    """Auto-save a game as HTML to local exports folder (for loop mode)."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Create exports directory if not exists
    EXPORTS_DIR.mkdir(exist_ok=True)

    # Get leaderboard for the report
    leaderboard = game_manager.get_leaderboard()

    # Generate HTML
    html = generate_game_html(game, leaderboard)

    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"partida_{timestamp}_{game_id[:8]}.html"
    filepath = EXPORTS_DIR / filename

    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return JSONResponse(content={
        "success": True,
        "filename": filename,
        "path": str(filepath)
    })


# WebSocket endpoint

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket connection for game updates."""
    await websocket.accept()

    # Add to active connections
    if game_id not in active_connections:
        active_connections[game_id] = []
    active_connections[game_id].append(websocket)

    # Broadcast function for this game
    async def broadcast(message: dict):
        connections = active_connections.get(game_id, [])
        for conn in connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass

    # Create game controller if not exists
    if game_id not in game_controllers:
        game_controllers[game_id] = GameController(
            game_id=game_id,
            llm_call=call_llm,
            broadcast=broadcast
        )

    controller = game_controllers[game_id]

    try:
        # Send current game state
        game = game_manager.get_game(game_id)
        if game:
            # For human player, send their word
            human_player = next((p for p in game.players if p.is_human), None)
            word_for_human = human_player.word if human_player else None

            # Get impostor for spectator view
            impostor = next((p for p in game.players if p.is_impostor), None)

            await websocket.send_json({
                "type": "game_state",
                "data": {
                    "id": game.id,
                    "phase": game.phase.value,
                    "mode": game.mode.value,
                    "current_round": game.current_round,
                    "debate_duration": game.debate_duration,
                    "your_word": word_for_human,
                    "secret_word": game.secret_word,
                    "impostor_id": game.impostor_id,
                    "impostor_name": impostor.display_name if impostor else None,
                    "players": [
                        {
                            "id": p.id,
                            "display_name": p.display_name,
                            "model": p.model,
                            "color": p.color,
                            "is_human": p.is_human,
                            "is_eliminated": p.is_eliminated,
                            "words_said": p.words_said,
                        }
                        for p in game.players
                    ]
                }
            })

        # Handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            msg_data = message.get("data", {})

            if msg_type == "start_game":
                # Start the game
                asyncio.create_task(controller.start_game())

            elif msg_type == "player_word":
                # Human player submits a word
                word = msg_data.get("word", "")
                await controller.handle_human_word(word)

            elif msg_type == "debate_message":
                # Human player sends debate message
                message = msg_data.get("message", "")
                await controller.handle_human_debate_message(message)

            elif msg_type == "cast_vote":
                # Human player votes
                voted_for = msg_data.get("voted_for", "")
                await controller.handle_human_vote(voted_for)

            elif msg_type == "impostor_guess":
                # Human impostor guesses the word
                guess = msg_data.get("guess", "")
                await controller.handle_human_impostor_guess(guess)

    except WebSocketDisconnect:
        # Remove from active connections
        if game_id in active_connections:
            active_connections[game_id] = [
                conn for conn in active_connections[game_id]
                if conn != websocket
            ]


# Serve frontend static files (if built)
try:
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse("../frontend/dist/index.html")

    @app.get("/{path:path}")
    async def serve_frontend_paths(path: str):
        return FileResponse("../frontend/dist/index.html")
except Exception:
    # Frontend not built yet
    @app.get("/")
    async def root():
        return {"message": "Impostor LLM Game API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

