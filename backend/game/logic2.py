"""
Game flow logic for the Impostor Word Game - Version 2
Uses chat-based context management for persistent player memory.

Each AI player maintains a full conversation history throughout the game,
allowing them to remember everything that happened and make better decisions.
"""
import asyncio
from typing import Optional, Callable, Awaitable
from models.schemas import GameState, GamePhase, Player
from game.state import game_manager
from game.prompts2 import (
    GameConversationManager,
    PlayerConversation,
    get_word_from_player,
    get_debate_message_from_player,
    get_vote_from_player,
    get_impostor_guess,
    format_round_start,
    format_debate_start,
    format_voting_start,
    format_game_result,
    censor_secret_word,
)
from game.prompts import clean_llm_response, is_valid_word
from llm.ollama_client import ollama_client


class GameController2:
    """
    Controls the game flow using chat-based context management.

    Unlike GameController (logic.py), this version maintains persistent
    conversation history for each AI player throughout the entire game.
    """

    def __init__(
        self,
        game_id: str,
        llm_call: Callable[[str, str], Awaitable[str]],  # Kept for API compatibility
        broadcast: Callable[[dict], Awaitable[None]],
    ):
        self.game_id = game_id
        self.broadcast = broadcast  # WebSocket broadcast to UI
        self._debate_task: Optional[asyncio.Task] = None
        self._tie_attempts = 0
        self._ai_voting_complete = False
        self._human_vote_pending = None

        # Chat-based context manager - initialized when game starts
        self.conversation_manager: Optional[GameConversationManager] = None

    @property
    def game(self) -> Optional[GameState]:
        return game_manager.get_game(self.game_id)

    def _init_conversations(self):
        """Initialize conversation manager and player conversations."""
        game = self.game
        if not game:
            return

        self.conversation_manager = GameConversationManager(self.game_id)

        for player in game.players:
            if player.is_human:
                continue  # Human players don't need LLM conversations

            self.conversation_manager.init_player(
                player_id=player.id,
                player_name=player.display_name,
                model=player.model,
                is_impostor=player.is_impostor,
                secret_word=None if player.is_impostor else game.secret_word
            )

    def _get_conversation(self, player_id: str) -> Optional[PlayerConversation]:
        """Get a player's conversation, returns None for human players."""
        if not self.conversation_manager:
            return None
        return self.conversation_manager.get_conversation(player_id)

    async def start_game(self):
        """Start the game flow."""
        game = game_manager.start_game(self.game_id)
        if not game:
            return

        # Initialize conversation manager with all AI players
        self._init_conversations()

        # Log game setup for debugging
        impostor = next((p for p in game.players if p.is_impostor), None)
        print(f"\n{'='*60}", flush=True)
        print(f"[GAME START v2] Palabra secreta: '{game.secret_word}'", flush=True)
        print(f"[GAME START v2] Impostor: {impostor.display_name if impostor else 'N/A'}", flush=True)
        print(f"[GAME START v2] Jugadores: {[p.display_name for p in game.players]}", flush=True)
        print(f"[GAME START v2] Usando contexto persistente por jugador", flush=True)
        print(f"{'='*60}\n", flush=True)

        await self.broadcast({
            "type": "phase_change",
            "data": {"phase": GamePhase.WORD_REVEAL.value}
        })

        # Wait for word reveal animation
        await asyncio.sleep(3)

        # Advance to word round
        game_manager.advance_to_word_round(self.game_id)
        await self.broadcast({
            "type": "phase_change",
            "data": {"phase": GamePhase.WORD_ROUND.value}
        })

        # Broadcast round start to all AI conversations
        if self.conversation_manager:
            self.conversation_manager.broadcast_to_all(
                format_round_start(game.current_round)
            )

        # Start word round
        await self.run_word_round()

    async def run_word_round(self, start_from: int = 0):
        """Run the word round where each player says a word."""
        game = self.game
        if not game:
            return

        active_players = [p for p in game.players if not p.is_eliminated]

        for i in range(start_from, len(active_players)):
            player = active_players[i]
            game.current_player_index = i

            await self.broadcast({
                "type": "player_turn",
                "data": {
                    "player_id": player.id,
                    "player_name": player.display_name
                }
            })

            if player.is_human:
                # Wait for human input (handled via WebSocket)
                return

            # AI player
            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": True}
            })

            # Get previous words for context
            previous_words = []
            for p in active_players[:i]:
                if p.words_said:
                    previous_words.append((p.display_name, p.words_said[-1]))

            # Get player's conversation
            conversation = self._get_conversation(player.id)
            if not conversation:
                print(f"[ERROR] No conversation for {player.display_name}")
                continue

            try:
                # Use the new chat-based function
                word = await get_word_from_player(
                    conversation,
                    ollama_client,
                    round_number=game.current_round,
                    turn_number=i + 1,
                    previous_words=previous_words
                )

                # Fallback if empty
                if not word:
                    word = "..."

                is_impostor = "[IMPOSTOR]" if player.is_impostor else "[OK]"
                print(f"[WORD v2] {player.display_name} {is_impostor}: '{word}'", flush=True)

            except Exception as e:
                print(f"[ERROR] Word round error for {player.display_name}: {e}")
                import traceback
                traceback.print_exc()
                word = "..."

            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": False}
            })

            # Record the word in game state
            game_manager.record_player_word(self.game_id, player.id, word)

            # Broadcast to UI
            await self.broadcast({
                "type": "player_word",
                "data": {
                    "player_id": player.id,
                    "player_name": player.display_name,
                    "word": word
                }
            })

            # Broadcast to all other AI conversations
            if self.conversation_manager:
                self.conversation_manager.broadcast_word(player.id, player.display_name, word)

            await asyncio.sleep(1)

        # All players have spoken, move to debate
        await self.start_debate()

    async def handle_human_word(self, word: str):
        """Handle when a human player submits their word."""
        game = self.game
        if not game or game.phase != GamePhase.WORD_ROUND:
            return

        active_players = [p for p in game.players if not p.is_eliminated]
        current_index = game.current_player_index
        current_player = active_players[current_index]

        if not current_player.is_human:
            return

        # Record the word
        game_manager.record_player_word(self.game_id, current_player.id, word)

        # Broadcast to UI
        await self.broadcast({
            "type": "player_word",
            "data": {
                "player_id": current_player.id,
                "player_name": current_player.display_name,
                "word": word
            }
        })

        # Broadcast to all AI conversations so they know what human said
        if self.conversation_manager:
            self.conversation_manager.broadcast_word(
                current_player.id,
                current_player.display_name,
                word
            )

        # Continue with remaining players
        await self.run_word_round(start_from=current_index + 1)

    async def start_debate(self):
        """Start the debate phase."""
        game = self.game
        if not game:
            return

        game.phase = GamePhase.DEBATE

        # Broadcast debate start to AI conversations
        if self.conversation_manager:
            self.conversation_manager.broadcast_to_all(format_debate_start())

        await self.broadcast({
            "type": "phase_change",
            "data": {
                "phase": GamePhase.DEBATE.value,
                "duration": game.debate_duration
            }
        })

        # Run debate
        self._debate_task = asyncio.create_task(self._run_debate())

    async def _run_debate(self):
        """Run the debate with 5 rounds - each player speaks 5 times."""
        game = self.game
        if not game:
            return

        active_players = [p for p in game.players if not p.is_eliminated]
        num_rounds = 5

        for round_num in range(num_rounds):
            await self.broadcast({
                "type": "debate_round",
                "data": {"round": round_num + 1, "total": num_rounds}
            })

            for player in active_players:
                if player.is_human:
                    continue

                await self.broadcast({
                    "type": "ai_thinking",
                    "data": {"player_id": player.id, "thinking": True}
                })

                # Get all words said for context
                all_words = []
                for p in active_players:
                    if p.words_said:
                        all_words.append((p.display_name, ", ".join(p.words_said)))

                # Get player lists
                active_names = [p.display_name for p in active_players]
                eliminated_names = [p.display_name for p in game.players if p.is_eliminated]

                conversation = self._get_conversation(player.id)
                if not conversation:
                    continue

                try:
                    # Use the new chat-based function
                    message = await get_debate_message_from_player(
                        conversation,
                        ollama_client,
                        active_players=active_names,
                        eliminated_players=eliminated_names if eliminated_names else None,
                        all_words=all_words
                    )

                    # Censor secret word if accidentally said
                    message = censor_secret_word(message, game.secret_word)

                    if not message or len(message) < 3:
                        message = "Estoy analizando la situacion..."

                except Exception as e:
                    print(f"[ERROR] Debate error for {player.display_name}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    message = "Hmm, no estoy seguro."

                await self.broadcast({
                    "type": "ai_thinking",
                    "data": {"player_id": player.id, "thinking": False}
                })

                # Record in game state
                game_manager.add_debate_message(self.game_id, player.id, message)

                # Broadcast to UI
                await self.broadcast({
                    "type": "new_debate_message",
                    "data": {
                        "player_id": player.id,
                        "player_name": player.display_name,
                        "message": message
                    }
                })

                # Broadcast to other AI conversations
                if self.conversation_manager:
                    self.conversation_manager.broadcast_debate_message(
                        player.id,
                        player.display_name,
                        message
                    )

                await asyncio.sleep(1)

        # Debate ended
        await self.broadcast({
            "type": "debate_ended",
            "data": {"message": "El debate ha terminado. Hora de votar."}
        })

        # Broadcast voting start to AI conversations
        if self.conversation_manager:
            self.conversation_manager.broadcast_to_all(format_voting_start())

        await asyncio.sleep(2)
        await self.start_voting()

    async def handle_human_debate_message(self, message: str):
        """Handle when a human player sends a debate message."""
        game = self.game
        if not game or game.phase != GamePhase.DEBATE:
            return

        human_player = next((p for p in game.players if p.is_human), None)
        if not human_player:
            return

        # Record in game state
        game_manager.add_debate_message(self.game_id, human_player.id, message)

        # Broadcast to UI
        await self.broadcast({
            "type": "new_debate_message",
            "data": {
                "player_id": human_player.id,
                "player_name": human_player.display_name,
                "message": message
            }
        })

        # Broadcast to all AI conversations
        if self.conversation_manager:
            self.conversation_manager.broadcast_debate_message(
                human_player.id,
                human_player.display_name,
                message
            )

    async def start_voting(self):
        """Start the voting phase."""
        game = game_manager.start_voting(self.game_id)
        if not game:
            return

        self._ai_voting_complete = False
        self._human_vote_pending = None

        await self.broadcast({
            "type": "phase_change",
            "data": {"phase": GamePhase.VOTING.value}
        })

        active_players = [p for p in game.players if not p.is_eliminated]

        for player in active_players:
            if player.is_human:
                continue

            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": True}
            })

            # Get all words (excluding self)
            all_words = [
                (p.display_name, ", ".join(p.words_said))
                for p in active_players
                if p.id != player.id
            ]

            # Valid players to vote for (excluding self)
            votable_names = [p.display_name for p in active_players if p.id != player.id]
            eliminated_names = [p.display_name for p in game.players if p.is_eliminated]

            conversation = self._get_conversation(player.id)
            if not conversation:
                continue

            try:
                # Use the new chat-based function
                voted_for_name, justification = await get_vote_from_player(
                    conversation,
                    ollama_client,
                    votable_players=votable_names,
                    all_words=all_words,
                    eliminated_players=eliminated_names if eliminated_names else None
                )

                print(f"[VOTE v2] {player.display_name} -> {voted_for_name} | Razon: {justification[:80]}...", flush=True)

                # Find player by name
                voted_for = next(
                    (p for p in active_players if p.display_name.lower() == voted_for_name.lower()),
                    None
                )

                if voted_for and voted_for.id != player.id:
                    game_manager.record_vote(self.game_id, player.id, voted_for.id, justification)
                else:
                    # Invalid vote, vote randomly
                    import random
                    others = [p for p in active_players if p.id != player.id]
                    voted_for = random.choice(others)
                    justification = "No pude decidir claramente."
                    print(f"[VOTE v2] {player.display_name} -> {voted_for.display_name} (RANDOM)", flush=True)
                    game_manager.record_vote(self.game_id, player.id, voted_for.id, justification)

            except Exception as e:
                print(f"[VOTE ERROR] {player.display_name}: {e}", flush=True)
                import random
                others = [p for p in active_players if p.id != player.id]
                voted_for = random.choice(others)
                justification = "Error al procesar mi voto."
                game_manager.record_vote(self.game_id, player.id, voted_for.id, justification)

            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": False}
            })

            # Broadcast vote to UI
            await self.broadcast({
                "type": "player_voted",
                "data": {
                    "voter_id": player.id,
                    "voter_name": player.display_name,
                    "voted_for_name": voted_for.display_name,
                    "justification": justification
                }
            })

            # Broadcast vote to AI conversations
            if self.conversation_manager:
                self.conversation_manager.broadcast_vote(
                    player.display_name,
                    voted_for.display_name,
                    justification
                )

            await asyncio.sleep(0.5)

        self._ai_voting_complete = True

        # Check if all non-human players have voted
        game = self.game
        human_player = next((p for p in game.players if p.is_human and not p.is_eliminated), None)
        if not human_player:
            await self.process_elimination()
        elif self._human_vote_pending:
            voted_for_id = self._human_vote_pending
            self._human_vote_pending = None
            await self._complete_human_vote(human_player, voted_for_id)

    async def handle_human_vote(self, voted_for_id: str):
        """Handle when a human player votes."""
        game = self.game
        if not game or game.phase != GamePhase.VOTING:
            return

        human_player = next((p for p in game.players if p.is_human), None)
        if not human_player:
            return

        if not self._ai_voting_complete:
            self._human_vote_pending = voted_for_id
            voted_for = next((p for p in game.players if p.id == voted_for_id), None)
            if voted_for:
                await self.broadcast({
                    "type": "player_voted",
                    "data": {
                        "voter_id": human_player.id,
                        "voter_name": human_player.display_name,
                        "voted_for_name": voted_for.display_name,
                        "justification": ""
                    }
                })
            return

        await self._complete_human_vote(human_player, voted_for_id)

    async def _complete_human_vote(self, human_player, voted_for_id: str):
        """Complete the human vote and process elimination."""
        game = self.game
        if not game:
            return

        voted_for = next((p for p in game.players if p.id == voted_for_id), None)
        if not voted_for:
            return

        game_manager.record_vote(self.game_id, human_player.id, voted_for_id, "Voto del jugador humano")

        if not self._human_vote_pending:
            await self.broadcast({
                "type": "player_voted",
                "data": {
                    "voter_id": human_player.id,
                    "voter_name": human_player.display_name,
                    "voted_for_name": voted_for.display_name,
                    "justification": ""
                }
            })

        # Broadcast human vote to AI conversations
        if self.conversation_manager:
            self.conversation_manager.broadcast_vote(
                human_player.display_name,
                voted_for.display_name,
                "Voto del jugador humano"
            )

        await self.process_elimination()

    async def process_elimination(self):
        """Process the elimination vote results."""
        game, eliminated_id, is_tie = game_manager.process_elimination(self.game_id)
        if not game:
            return

        if is_tie:
            self._tie_attempts += 1
            print(f"[INFO] Voting tie detected, attempt {self._tie_attempts}")

            if self._tie_attempts >= 2:
                eliminated_id = game_manager.break_tie_randomly(self.game_id)
                print(f"[INFO] Breaking tie randomly, eliminated: {eliminated_id}")
                self._tie_attempts = 0
                game = self.game
            else:
                await self.broadcast({
                    "type": "vote_result",
                    "data": {"tie": True, "message": "Empate! Votando de nuevo..."}
                })
                await asyncio.sleep(2)
                await self.start_voting()
                return

        self._tie_attempts = 0

        eliminated_player = next(
            (p for p in game.players if p.id == eliminated_id),
            None
        )

        # Broadcast elimination to AI conversations
        if self.conversation_manager and eliminated_player:
            self.conversation_manager.broadcast_elimination(
                eliminated_player.display_name,
                eliminated_id == game.impostor_id
            )

        await self.broadcast({
            "type": "elimination",
            "data": {
                "eliminated_id": eliminated_id,
                "eliminated_name": eliminated_player.display_name if eliminated_player else "",
                "was_impostor": eliminated_id == game.impostor_id,
                "votes": [{"voter": v.voter_id, "voted_for": v.voted_for_id} for v in game.votes]
            }
        })

        await asyncio.sleep(3)

        if game.phase == GamePhase.IMPOSTOR_GUESS:
            await self.handle_impostor_guess_phase()
        elif game.phase == GamePhase.GAME_OVER:
            await self.broadcast_game_over()
        else:
            # Continue to next round
            if self.conversation_manager:
                self.conversation_manager.broadcast_to_all(
                    format_round_start(game.current_round)
                )

            await self.broadcast({
                "type": "phase_change",
                "data": {"phase": GamePhase.WORD_ROUND.value, "round": game.current_round}
            })
            await self.run_word_round()

    async def handle_impostor_guess_phase(self):
        """Handle the impostor's guess phase."""
        game = self.game
        if not game:
            return

        await self.broadcast({
            "type": "phase_change",
            "data": {"phase": GamePhase.IMPOSTOR_GUESS.value}
        })

        impostor = next((p for p in game.players if p.is_impostor), None)
        if not impostor:
            return

        if impostor.is_human:
            return

        await self.broadcast({
            "type": "ai_thinking",
            "data": {"player_id": impostor.id, "thinking": True}
        })

        # Get all words said
        all_words = [
            (p.display_name, ", ".join(p.words_said))
            for p in game.players
        ]

        # Get debate history
        debate_history = [
            (msg.player_name, msg.message)
            for msg in game.debate_messages
        ]

        conversation = self._get_conversation(impostor.id)
        if not conversation:
            print(f"[ERROR] No conversation for impostor {impostor.display_name}")
            guess = "no se"
        else:
            try:
                guess = await get_impostor_guess(
                    conversation,
                    ollama_client,
                    all_words,
                    debate_history
                )
                print(f"[GUESS v2] {impostor.display_name} guesses: '{guess}'", flush=True)
            except Exception as e:
                print(f"[ERROR] Impostor guess error: {e}")
                guess = "no se"

        await self.broadcast({
            "type": "ai_thinking",
            "data": {"player_id": impostor.id, "thinking": False}
        })

        game_manager.process_impostor_guess(self.game_id, guess)

        await self.broadcast({
            "type": "impostor_guess",
            "data": {
                "guess": guess,
                "correct": game.result.value == "impostor_wins_guess",
                "secret_word": game.secret_word
            }
        })

        await asyncio.sleep(3)
        await self.broadcast_game_over()

    async def handle_human_impostor_guess(self, guess: str):
        """Handle when a human impostor guesses the word."""
        game = self.game
        if not game or game.phase != GamePhase.IMPOSTOR_GUESS:
            return

        game_manager.process_impostor_guess(self.game_id, guess)

        await self.broadcast({
            "type": "impostor_guess",
            "data": {
                "guess": guess,
                "correct": game.result.value == "impostor_wins_guess",
                "secret_word": game.secret_word
            }
        })

        await asyncio.sleep(3)
        await self.broadcast_game_over()

    async def broadcast_game_over(self):
        """Broadcast the game over state."""
        game = self.game
        if not game:
            return

        # Broadcast game result to AI conversations
        if self.conversation_manager:
            impostor = next((p for p in game.players if p.is_impostor), None)
            result_msg = format_game_result(
                game.winner,
                game.secret_word,
                impostor.display_name if impostor else "?"
            )
            self.conversation_manager.broadcast_to_all(result_msg)

        leaderboard = game_manager.get_leaderboard()

        await self.broadcast({
            "type": "game_over",
            "data": {
                "result": game.result.value,
                "winner": game.winner,
                "secret_word": game.secret_word,
                "impostor_id": game.impostor_id,
                "impostor_guess": game.impostor_guess,
                "leaderboard": leaderboard
            }
        })
