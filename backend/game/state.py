"""
Game state management for the Impostor Word Game
"""
import random
import uuid
from typing import Optional
from models.schemas import (
    GameState, Player, GamePhase, GameMode, GameResult,
    DebateMessage, Vote, GameConfig
)
from game.words import get_random_word
from llm.players import LLM_PLAYERS, DEFAULT_PLAYERS, get_player_config, get_single_model_configs

# Points configuration
POINTS = {
    "vote_correct": 10,       # Innocent votes correctly for impostor
    "impostor_eliminated": 5,  # All innocents get this when impostor caught
    "impostor_guessed": -5,    # Innocents lose if impostor guesses word
    "impostor_survive_round": 8,  # Impostor survives a round
    "impostor_not_found": 15,  # Impostor wins by not being found
    "impostor_guess_word": 20,  # Impostor guesses the word correctly
    "eliminated_innocent": -3,  # Innocent gets eliminated
}


class GameManager:
    """Manages game state and logic."""

    def __init__(self):
        self.games: dict[str, GameState] = {}
        self.leaderboard: dict[str, dict] = {}  # model -> stats
        self._init_leaderboard()

    def _init_leaderboard(self):
        """Initialize leaderboard with all LLM players."""
        for player in LLM_PLAYERS:
            self.leaderboard[player.model] = {
                "model": player.model,
                "display_name": player.display_name,
                "color": player.color,
                "score": 0,
                "games_played": 0,
                "wins_as_innocent": 0,
                "wins_as_impostor": 0,
                "times_impostor": 0,
                "correct_guesses": 0,
                "correct_votes": 0,
                "total_votes": 0,
            }

    def create_game(self, config: GameConfig) -> GameState:
        """Create a new game with the given configuration."""
        game_id = str(uuid.uuid4())[:8]

        # Check for single-model mode
        if config.single_model:
            # Use the same model for all players with different names
            player_count = max(3, min(6, config.player_count))
            player_configs = get_single_model_configs(config.single_model, player_count)
        else:
            # Determine which players to use (normal mode)
            selected_names = config.selected_players if config.selected_players else DEFAULT_PLAYERS

            # Filter LLM_PLAYERS to only selected ones
            player_configs = [p for p in LLM_PLAYERS if p.display_name in selected_names]

            # Ensure at least 3 players
            if len(player_configs) < 3:
                player_configs = [p for p in LLM_PLAYERS if p.display_name in DEFAULT_PLAYERS[:3]]

        random.shuffle(player_configs)

        # Create players
        players = []
        for i, p_config in enumerate(player_configs):
            is_human = config.mode == GameMode.HUMAN_PLAYER and i == config.human_position
            player = Player(
                id=f"player_{i}",
                model=p_config.model if not is_human else "human",
                display_name=p_config.display_name if not is_human else config.human_name,
                color=p_config.color if not is_human else "#FFD700",
                is_human=is_human,
            )
            players.append(player)

        # Select random impostor
        impostor_index = random.randint(0, len(players) - 1)
        players[impostor_index].is_impostor = True

        # Get secret word
        secret_word = get_random_word()

        # Assign words to players
        for player in players:
            if player.is_impostor:
                player.word = "IMPOSTOR"
            else:
                player.word = secret_word

        game = GameState(
            id=game_id,
            phase=GamePhase.SETUP,
            mode=config.mode,
            players=players,
            secret_word=secret_word,
            impostor_id=players[impostor_index].id,
            debate_duration=config.debate_duration,
        )

        self.games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get a game by ID."""
        return self.games.get(game_id)

    def start_game(self, game_id: str) -> Optional[GameState]:
        """Start the game (transition from SETUP to WORD_REVEAL)."""
        game = self.games.get(game_id)
        if game and game.phase == GamePhase.SETUP:
            game.phase = GamePhase.WORD_REVEAL
        return game

    def advance_to_word_round(self, game_id: str) -> Optional[GameState]:
        """Advance from WORD_REVEAL to WORD_ROUND."""
        game = self.games.get(game_id)
        if game and game.phase == GamePhase.WORD_REVEAL:
            game.phase = GamePhase.WORD_ROUND
            game.current_player_index = 0
            # Randomize player order
            active_players = [p for p in game.players if not p.is_eliminated]
            random.shuffle(active_players)
            # Reorder players list while keeping eliminated at the end
            eliminated = [p for p in game.players if p.is_eliminated]
            game.players = active_players + eliminated
        return game

    def record_player_word(self, game_id: str, player_id: str, word: str) -> Optional[GameState]:
        """Record a word said by a player."""
        game = self.games.get(game_id)
        if not game or game.phase != GamePhase.WORD_ROUND:
            return None

        for player in game.players:
            if player.id == player_id:
                player.words_said.append(word)
                break

        # Move to next player
        game.current_player_index += 1
        active_players = [p for p in game.players if not p.is_eliminated]

        if game.current_player_index >= len(active_players):
            # All players have spoken, move to debate
            game.phase = GamePhase.DEBATE
            game.current_player_index = 0

        return game

    def add_debate_message(self, game_id: str, player_id: str, message: str) -> Optional[GameState]:
        """Add a debate message."""
        game = self.games.get(game_id)
        if not game or game.phase != GamePhase.DEBATE:
            return None

        player = next((p for p in game.players if p.id == player_id), None)
        if player:
            import time
            game.debate_messages.append(DebateMessage(
                player_id=player_id,
                player_name=player.display_name,
                message=message,
                timestamp=time.time()
            ))

        return game

    def start_voting(self, game_id: str) -> Optional[GameState]:
        """Transition to VOTING phase (from DEBATE or after tie in ELIMINATION)."""
        game = self.games.get(game_id)
        if game and game.phase in (GamePhase.DEBATE, GamePhase.ELIMINATION):
            game.phase = GamePhase.VOTING
            game.votes = []  # Clear votes for fresh voting
        return game

    def record_vote(self, game_id: str, voter_id: str, voted_for_id: str, justification: str = "") -> Optional[GameState]:
        """Record a vote with justification."""
        game = self.games.get(game_id)
        if not game or game.phase != GamePhase.VOTING:
            return None

        # Check if already voted
        if any(v.voter_id == voter_id for v in game.votes):
            return game

        game.votes.append(Vote(voter_id=voter_id, voted_for_id=voted_for_id, justification=justification))

        # Check if all active players have voted
        active_players = [p for p in game.players if not p.is_eliminated]
        if len(game.votes) >= len(active_players):
            game.phase = GamePhase.ELIMINATION

        return game

    def process_elimination(self, game_id: str) -> tuple[Optional[GameState], Optional[str], bool]:
        """
        Process the elimination phase.
        Returns: (game_state, eliminated_player_id, is_tie)
        """
        game = self.games.get(game_id)
        if not game or game.phase != GamePhase.ELIMINATION:
            return None, None, False

        # Count votes
        vote_counts: dict[str, int] = {}
        for vote in game.votes:
            vote_counts[vote.voted_for_id] = vote_counts.get(vote.voted_for_id, 0) + 1

        if not vote_counts:
            return game, None, False

        # Find max votes
        max_votes = max(vote_counts.values())
        most_voted = [pid for pid, count in vote_counts.items() if count == max_votes]

        if len(most_voted) > 1:
            # Tie - need revote
            return game, None, True

        eliminated_id = most_voted[0]

        # Mark player as eliminated
        for player in game.players:
            if player.id == eliminated_id:
                player.is_eliminated = True
                break

        game.eliminated_players.append(eliminated_id)

        # Check if eliminated was impostor
        if eliminated_id == game.impostor_id:
            # Impostor caught! Give them a chance to guess
            game.phase = GamePhase.IMPOSTOR_GUESS
        else:
            # Wrong person eliminated
            # Update points for eliminated innocent
            self._update_player_points(game, eliminated_id, POINTS["eliminated_innocent"])

            # Check if enough players remain
            active_non_impostor = [
                p for p in game.players
                if not p.is_eliminated and not p.is_impostor
            ]
            if len(active_non_impostor) <= 1:
                # Impostor wins by elimination
                self._end_game(game, GameResult.IMPOSTOR_WINS_HIDDEN)
            else:
                # Continue to next round
                game.current_round += 1
                game.phase = GamePhase.WORD_ROUND
                game.current_player_index = 0
                game.debate_messages = []
                game.votes = []

        return game, eliminated_id, False

    def break_tie_randomly(self, game_id: str) -> Optional[str]:
        """Break a voting tie by randomly selecting from tied players."""
        game = self.games.get(game_id)
        if not game:
            return None

        # Count votes
        vote_counts: dict[str, int] = {}
        for vote in game.votes:
            vote_counts[vote.voted_for_id] = vote_counts.get(vote.voted_for_id, 0) + 1

        if not vote_counts:
            return None

        # Find max votes and tied players
        max_votes = max(vote_counts.values())
        tied_players = [pid for pid, count in vote_counts.items() if count == max_votes]

        # Randomly pick one
        eliminated_id = random.choice(tied_players)

        # Mark player as eliminated
        for player in game.players:
            if player.id == eliminated_id:
                player.is_eliminated = True
                break

        game.eliminated_players.append(eliminated_id)

        # Check if eliminated was impostor
        if eliminated_id == game.impostor_id:
            game.phase = GamePhase.IMPOSTOR_GUESS
        else:
            # Wrong person eliminated
            self._update_player_points(game, eliminated_id, POINTS["eliminated_innocent"])

            # Check if enough players remain
            active_non_impostor = [
                p for p in game.players
                if not p.is_eliminated and not p.is_impostor
            ]
            if len(active_non_impostor) <= 1:
                self._end_game(game, GameResult.IMPOSTOR_WINS_HIDDEN)
            else:
                # Continue to next round
                game.current_round += 1
                game.phase = GamePhase.WORD_ROUND
                game.current_player_index = 0
                game.debate_messages = []
                game.votes = []

        return eliminated_id

    def process_impostor_guess(self, game_id: str, guess: str) -> Optional[GameState]:
        """Process the impostor's guess of the secret word."""
        from game.words import is_word_match

        game = self.games.get(game_id)
        if not game or game.phase != GamePhase.IMPOSTOR_GUESS:
            return None

        game.impostor_guess = guess

        if is_word_match(guess, game.secret_word):
            # Impostor guessed correctly!
            self._end_game(game, GameResult.IMPOSTOR_WINS_GUESS)
        else:
            # Impostor failed to guess
            self._end_game(game, GameResult.INNOCENTS_WIN)

        return game

    def _end_game(self, game: GameState, result: GameResult):
        """End the game and calculate final scores."""
        game.phase = GamePhase.GAME_OVER
        game.result = result

        if result == GameResult.INNOCENTS_WIN:
            game.winner = "innocents"
            # Update scores for innocents
            for player in game.players:
                if not player.is_impostor:
                    self._update_player_points(game, player.id, POINTS["impostor_eliminated"])
                    # Bonus for correct votes
                    correct_vote = any(
                        v.voter_id == player.id and v.voted_for_id == game.impostor_id
                        for v in game.votes
                    )
                    if correct_vote:
                        self._update_player_points(game, player.id, POINTS["vote_correct"])
                        self._increment_stat(player.model, "correct_votes")
                    self._increment_stat(player.model, "total_votes")
                    self._increment_stat(player.model, "wins_as_innocent")
                else:
                    self._increment_stat(player.model, "times_impostor")

        elif result == GameResult.IMPOSTOR_WINS_GUESS:
            game.winner = "impostor"
            # Impostor gets bonus for guessing
            impostor = next(p for p in game.players if p.is_impostor)
            self._update_player_points(game, impostor.id, POINTS["impostor_guess_word"])
            self._increment_stat(impostor.model, "correct_guesses")
            self._increment_stat(impostor.model, "wins_as_impostor")
            self._increment_stat(impostor.model, "times_impostor")
            # Innocents lose points
            for player in game.players:
                if not player.is_impostor:
                    self._update_player_points(game, player.id, POINTS["impostor_guessed"])

        elif result == GameResult.IMPOSTOR_WINS_HIDDEN:
            game.winner = "impostor"
            impostor = next(p for p in game.players if p.is_impostor)
            self._update_player_points(game, impostor.id, POINTS["impostor_not_found"])
            self._increment_stat(impostor.model, "wins_as_impostor")
            self._increment_stat(impostor.model, "times_impostor")

        # Update games played for all
        for player in game.players:
            if not player.is_human:
                self._increment_stat(player.model, "games_played")

    def _update_player_points(self, game: GameState, player_id: str, points: int):
        """Update a player's score."""
        for player in game.players:
            if player.id == player_id:
                player.score += points
                if not player.is_human and player.model in self.leaderboard:
                    self.leaderboard[player.model]["score"] += points
                break

    def _increment_stat(self, model: str, stat: str):
        """Increment a leaderboard stat."""
        if model in self.leaderboard and stat in self.leaderboard[model]:
            self.leaderboard[model][stat] += 1

    def get_leaderboard(self) -> list[dict]:
        """Get the current leaderboard sorted by score."""
        entries = list(self.leaderboard.values())
        entries.sort(key=lambda x: x["score"], reverse=True)
        # Calculate vote accuracy
        for entry in entries:
            if entry["total_votes"] > 0:
                entry["vote_accuracy"] = round(
                    entry["correct_votes"] / entry["total_votes"] * 100, 1
                )
            else:
                entry["vote_accuracy"] = 0.0
        return entries

    def get_active_player(self, game: GameState) -> Optional[Player]:
        """Get the current active player."""
        active_players = [p for p in game.players if not p.is_eliminated]
        if game.current_player_index < len(active_players):
            return active_players[game.current_player_index]
        return None


# Global game manager instance
game_manager = GameManager()
