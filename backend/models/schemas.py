"""
Pydantic models for the Impostor Word Game
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class GamePhase(str, Enum):
    SETUP = "setup"
    WORD_REVEAL = "word_reveal"
    WORD_ROUND = "word_round"
    DEBATE = "debate"
    VOTING = "voting"
    ELIMINATION = "elimination"
    IMPOSTOR_GUESS = "impostor_guess"
    GAME_OVER = "game_over"


class GameMode(str, Enum):
    ALL_AI = "all_ai"  # 5 LLMs
    HUMAN_PLAYER = "human_player"  # 4 LLMs + 1 Human


class GameResult(str, Enum):
    INNOCENTS_WIN = "innocents_win"  # Impostor eliminated and didn't guess
    IMPOSTOR_WINS_HIDDEN = "impostor_wins_hidden"  # Impostor not found
    IMPOSTOR_WINS_GUESS = "impostor_wins_guess"  # Impostor guessed the word
    ONGOING = "ongoing"  # Game continues


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class Player(BaseModel):
    id: str
    model: str
    display_name: str
    color: str
    is_impostor: bool = False
    is_human: bool = False
    is_eliminated: bool = False
    word: str = ""
    words_said: list[str] = []
    current_vote: Optional[str] = None
    chat_history: list[ChatMessage] = []  # Conversation memory

    # Stats
    score: int = 0
    games_played: int = 0
    wins_as_innocent: int = 0
    wins_as_impostor: int = 0
    times_impostor: int = 0
    correct_guesses: int = 0
    correct_votes: int = 0
    total_votes: int = 0


class DebateMessage(BaseModel):
    player_id: str
    player_name: str
    message: str
    timestamp: float


class Vote(BaseModel):
    voter_id: str
    voted_for_id: str
    justification: str = ""  # Razon del voto


class GameState(BaseModel):
    id: str
    phase: GamePhase = GamePhase.SETUP
    mode: GameMode = GameMode.ALL_AI
    players: list[Player] = []
    secret_word: str = ""
    impostor_id: str = ""
    current_round: int = 1
    current_player_index: int = 0
    debate_messages: list[DebateMessage] = []
    votes: list[Vote] = []
    eliminated_players: list[str] = []
    debate_duration: int = 60  # seconds
    result: GameResult = GameResult.ONGOING
    impostor_guess: str = ""
    winner: str = ""  # "innocents" or "impostor"


# WebSocket message types
class WSMessageType(str, Enum):
    # Client -> Server
    START_GAME = "start_game"
    PLAYER_WORD = "player_word"
    DEBATE_MESSAGE = "debate_message"
    CAST_VOTE = "cast_vote"
    IMPOSTOR_GUESS = "impostor_guess"

    # Server -> Client
    GAME_STATE = "game_state"
    PHASE_CHANGE = "phase_change"
    PLAYER_TURN = "player_turn"
    WORD_REVEALED = "word_revealed"
    NEW_DEBATE_MESSAGE = "new_debate_message"
    VOTE_RESULT = "vote_result"
    ELIMINATION = "elimination"
    GAME_OVER = "game_over"
    ERROR = "error"
    AI_THINKING = "ai_thinking"


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict = {}


class GameConfig(BaseModel):
    mode: GameMode = GameMode.ALL_AI
    debate_duration: int = 60
    human_position: int = 0  # 0-4, only used in HUMAN_PLAYER mode
    selected_players: list[str] = []  # List of display_names to include (empty = use defaults)
    single_model: str = ""  # If set, use this model for all players (e.g., "qwen3:8b")
    player_count: int = 5  # Number of players for single_model mode (3-6)


class LeaderboardEntry(BaseModel):
    model: str
    display_name: str
    color: str
    score: int
    games_played: int
    wins_as_innocent: int
    wins_as_impostor: int
    times_impostor: int
    correct_guesses: int
    vote_accuracy: float
