"""
Game flow logic for the Impostor Word Game
"""
import asyncio
from typing import Optional, Callable, Awaitable
from models.schemas import GameState, GamePhase, Player, ChatMessage
from game.state import game_manager
from game.prompts import (
    format_word_round_prompt,
    format_debate_prompt,
    format_voting_prompt,
    format_impostor_guess_prompt,
    clean_llm_response,
    censor_secret_word,
    is_valid_word,
    parse_vote_response
)
from llm.ollama_client import call_llm_with_history


class GameController:
    """Controls the game flow and coordinates LLM calls."""

    def __init__(
        self,
        game_id: str,
        llm_call: Callable[[str, str], Awaitable[str]],
        broadcast: Callable[[dict], Awaitable[None]],
    ):
        self.game_id = game_id
        self.llm_call = llm_call
        self.broadcast = broadcast
        self._debate_task: Optional[asyncio.Task] = None
        self._tie_attempts = 0  # Track tie attempts to avoid infinite loops
        self._ai_voting_complete = False  # Flag to track AI voting completion
        self._human_vote_pending = None  # Store human vote if submitted early

    async def call_with_memory(self, player: Player, prompt: str) -> str:
        """Call LLM with conversation memory for this player."""
        # Convert player history to dict format
        history = [{"role": msg.role, "content": msg.content} for msg in player.chat_history]

        # Call LLM with history
        response, new_history = await call_llm_with_history(player.model, prompt, history)

        # Update player's history
        player.chat_history = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in new_history]

        return response

    @property
    def game(self) -> Optional[GameState]:
        return game_manager.get_game(self.game_id)

    async def start_game(self):
        """Start the game flow."""
        game = game_manager.start_game(self.game_id)
        if not game:
            return

        # Log game setup for debugging
        impostor = next((p for p in game.players if p.is_impostor), None)
        print(f"\n{'='*60}", flush=True)
        print(f"[GAME START] Palabra secreta: '{game.secret_word}'", flush=True)
        print(f"[GAME START] Impostor: {impostor.display_name if impostor else 'N/A'}", flush=True)
        print(f"[GAME START] Jugadores: {[p.display_name for p in game.players]}", flush=True)
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

        # Start word round
        await self.run_word_round()

    async def run_word_round(self, start_from: int = 0):
        """Run the word round where each player says a word.

        Args:
            start_from: Index to start from (used when resuming after human input)
        """
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
                # Store current index so we can resume from next player
                return

            # AI player
            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": True}
            })

            # Get previous words
            previous_words = []
            for p in active_players[:i]:
                if p.words_said:
                    previous_words.append((p.display_name, p.words_said[-1]))

            # Generate prompt and get response - different for impostor vs innocent
            prompt = format_word_round_prompt(
                player.display_name,
                player.word,
                previous_words,
                current_turn=i + 1,
                current_round=game.current_round,
                is_impostor=player.is_impostor
            )

            try:
                word = await self.call_with_memory(player, prompt)
                raw_word = word[:50] if len(word) > 50 else word
                word = self._clean_word_response(word)
                is_impostor = "[IMPOSTOR]" if player.is_impostor else "[OK]"
                print(f"[WORD] {player.display_name} {is_impostor}: '{raw_word}' -> '{word}'", flush=True)
            except Exception as e:
                print(f"[ERROR] Word round error for {player.display_name}: {e}")
                word = "..."  # Fallback

            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": False}
            })

            # Record the word
            game_manager.record_player_word(self.game_id, player.id, word)

            await self.broadcast({
                "type": "player_word",
                "data": {
                    "player_id": player.id,
                    "player_name": player.display_name,
                    "word": word
                }
            })

            await asyncio.sleep(1)  # Small delay between players

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

        await self.broadcast({
            "type": "player_word",
            "data": {
                "player_id": current_player.id,
                "player_name": current_player.display_name,
                "word": word
            }
        })

        # Continue with remaining players starting from NEXT index
        await self.run_word_round(start_from=current_index + 1)

    async def start_debate(self):
        """Start the debate phase."""
        game = self.game
        if not game:
            return

        game.phase = GamePhase.DEBATE
        await self.broadcast({
            "type": "phase_change",
            "data": {
                "phase": GamePhase.DEBATE.value,
                "duration": game.debate_duration
            }
        })

        # Run debate for the configured duration
        self._debate_task = asyncio.create_task(self._run_debate())

    async def _run_debate(self):
        """Run the debate with 5 rounds - each player speaks 5 times, then voting."""
        game = self.game
        if not game:
            return

        active_players = [p for p in game.players if not p.is_eliminated]
        num_rounds = 5  # Each AI speaks 5 times

        for round_num in range(num_rounds):
            # Broadcast round info
            await self.broadcast({
                "type": "debate_round",
                "data": {"round": round_num + 1, "total": num_rounds}
            })

            # Each player gets a turn per round
            for player in active_players:
                if player.is_human:
                    # Human can type anytime, skip in rotation
                    continue

                await self.broadcast({
                    "type": "ai_thinking",
                    "data": {"player_id": player.id, "thinking": True}
                })

                # Get all words said
                all_words = []
                for p in active_players:
                    if p.words_said:
                        all_words.append((p.display_name, ", ".join(p.words_said)))

                # Get debate history (last 10 messages for context)
                debate_history = [
                    (msg.player_name, msg.message)
                    for msg in game.debate_messages[-10:]
                ]

                # Get the word this player said in the word round
                player_said = player.words_said[-1] if player.words_said else ""

                # Get active and eliminated player names
                active_names = [p.display_name for p in active_players]
                eliminated_names = [p.display_name for p in game.players if p.is_eliminated]

                try:
                    prompt = format_debate_prompt(
                        player.display_name,
                        player.word,
                        all_words,
                        debate_history,
                        player_said_word=player_said,
                        active_players=active_names,
                        eliminated_players=eliminated_names
                    )

                    message = await self.call_with_memory(player, prompt)
                    message = self._clean_debate_response(message)
                    # Censor secret word if LLM accidentally says it
                    message = censor_secret_word(message, game.secret_word)
                except Exception as e:
                    print(f"[ERROR] Debate error for {player.display_name}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    message = "Hmm, no estoy seguro."

                await self.broadcast({
                    "type": "ai_thinking",
                    "data": {"player_id": player.id, "thinking": False}
                })

                game_manager.add_debate_message(self.game_id, player.id, message)

                await self.broadcast({
                    "type": "new_debate_message",
                    "data": {
                        "player_id": player.id,
                        "player_name": player.display_name,
                        "message": message
                    }
                })

                await asyncio.sleep(1)  # Delay between messages

        # Debate ended, announce voting
        await self.broadcast({
            "type": "debate_ended",
            "data": {"message": "El debate ha terminado. Hora de votar."}
        })
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

        game_manager.add_debate_message(self.game_id, human_player.id, message)

        await self.broadcast({
            "type": "new_debate_message",
            "data": {
                "player_id": human_player.id,
                "player_name": human_player.display_name,
                "message": message
            }
        })

    async def start_voting(self):
        """Start the voting phase."""
        game = game_manager.start_voting(self.game_id)
        if not game:
            return

        # Reset voting state
        self._ai_voting_complete = False
        self._human_vote_pending = None

        await self.broadcast({
            "type": "phase_change",
            "data": {"phase": GamePhase.VOTING.value}
        })

        # AI players vote
        active_players = [p for p in game.players if not p.is_eliminated]

        for player in active_players:
            if player.is_human:
                # Wait for human vote (handled via WebSocket)
                continue

            await self.broadcast({
                "type": "ai_thinking",
                "data": {"player_id": player.id, "thinking": True}
            })

            # Get all words said (excluding self)
            player_words = [
                (p.display_name, ", ".join(p.words_said))
                for p in active_players
                if p.id != player.id
            ]

            # Get FULL debate history (not just last 8 messages)
            full_debate = [
                (msg.player_name, msg.message)
                for msg in game.debate_messages
            ]

            # Get the word this player said
            player_said_word = player.words_said[-1] if player.words_said else ""

            # Get active and eliminated player names (excluding self for voting)
            active_names = [p.display_name for p in active_players if p.id != player.id]
            eliminated_names = [p.display_name for p in game.players if p.is_eliminated]

            # Format prompt with full context
            prompt = format_voting_prompt(
                player.display_name,
                player_words,
                full_debate,
                player_said_word,
                active_players=active_names,
                eliminated_players=eliminated_names
            )

            justification = ""
            try:
                vote_response = await self.call_with_memory(player, prompt)

                # Get valid names from active players (excluding self)
                valid_names = [p.display_name for p in active_players if p.id != player.id]

                # Parse vote and justification using new function
                voted_for_name, justification = parse_vote_response(vote_response, valid_names)

                # Log for debugging
                print(f"[VOTE] {player.display_name} raw: '{vote_response[:150]}...'", flush=True)
                print(f"[VOTE] {player.display_name} -> {voted_for_name} | Razon: {justification[:80]}...", flush=True)

                # Find player by name
                voted_for = next(
                    (p for p in active_players if p.display_name.lower() == voted_for_name.lower()),
                    None
                )
                if voted_for and voted_for.id != player.id:
                    game_manager.record_vote(self.game_id, player.id, voted_for.id, justification)
                else:
                    # Invalid vote, vote for random other player
                    others = [p for p in active_players if p.id != player.id]
                    import random
                    voted_for = random.choice(others)
                    justification = "No pude decidir claramente."
                    print(f"[VOTE] {player.display_name} -> {voted_for.display_name} (RANDOM)", flush=True)
                    game_manager.record_vote(self.game_id, player.id, voted_for.id, justification)
            except Exception as e:
                # Fallback: vote for random player
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

            # Broadcast the vote WITH justification
            await self.broadcast({
                "type": "player_voted",
                "data": {
                    "voter_id": player.id,
                    "voter_name": player.display_name,
                    "voted_for_name": voted_for.display_name,
                    "justification": justification
                }
            })

            await asyncio.sleep(0.5)

        # Mark AI voting as complete
        self._ai_voting_complete = True

        # Check if all non-human players have voted
        game = self.game
        human_player = next((p for p in game.players if p.is_human and not p.is_eliminated), None)
        if not human_player:
            # All AI, process elimination
            await self.process_elimination()
        elif self._human_vote_pending:
            # Human already voted while AIs were voting, process now
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

        # If AI voting is not complete yet, store the vote for later
        if not self._ai_voting_complete:
            self._human_vote_pending = voted_for_id
            # Still broadcast the vote so UI updates
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

        # AI voting is complete, process immediately
        await self._complete_human_vote(human_player, voted_for_id)

    async def _complete_human_vote(self, human_player, voted_for_id: str):
        """Complete the human vote and process elimination."""
        game = self.game
        if not game:
            return

        # Find who was voted for
        voted_for = next((p for p in game.players if p.id == voted_for_id), None)
        if not voted_for:
            return

        # Record the vote
        game_manager.record_vote(self.game_id, human_player.id, voted_for_id, "Voto del jugador humano")

        # Broadcast the human vote like AI votes (if not already broadcast)
        if not self._human_vote_pending:  # Only broadcast if not already done
            await self.broadcast({
                "type": "player_voted",
                "data": {
                    "voter_id": human_player.id,
                    "voter_name": human_player.display_name,
                    "voted_for_name": voted_for.display_name,
                    "justification": ""
                }
            })

        # Process elimination
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
                # After 2 ties, randomly pick from tied players
                eliminated_id = game_manager.break_tie_randomly(self.game_id)
                print(f"[INFO] Breaking tie randomly, eliminated: {eliminated_id}")
                self._tie_attempts = 0
                # Refresh game state after tie break
                game = self.game
            else:
                # Try voting again
                await self.broadcast({
                    "type": "vote_result",
                    "data": {"tie": True, "message": "Empate! Votando de nuevo..."}
                })
                await asyncio.sleep(2)
                await self.start_voting()
                return

        # Reset tie counter on successful elimination
        self._tie_attempts = 0

        # Broadcast elimination
        eliminated_player = next(
            (p for p in game.players if p.id == eliminated_id),
            None
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

        await asyncio.sleep(3)  # Dramatic pause

        if game.phase == GamePhase.IMPOSTOR_GUESS:
            # Impostor caught, give them a chance to guess
            await self.handle_impostor_guess_phase()
        elif game.phase == GamePhase.GAME_OVER:
            await self.broadcast_game_over()
        else:
            # Continue to next round
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
            # Wait for human input
            return

        # AI impostor guesses
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
            for msg in game.debate_messages[-10:]
        ]

        prompt = format_impostor_guess_prompt(impostor.display_name, all_words, debate_history)

        try:
            guess = await self.call_with_memory(impostor, prompt)
            guess = self._clean_word_response(guess)
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

    def _clean_word_response(self, response: str) -> str:
        """Clean the LLM word response."""
        # First remove thinking tags and artifacts
        response = clean_llm_response(response)

        # Try to find a valid word from the response
        words = response.strip().split() if response.strip() else []

        for w in words:
            # Clean punctuation
            cleaned = ''.join(c for c in w if c.isalnum() or c in 'áéíóúüñÁÉÍÓÚÜÑ')
            cleaned = cleaned.lower()
            if cleaned and is_valid_word(cleaned):
                return cleaned

        # Fallback if no valid word found
        return "..."

    def _clean_debate_response(self, response: str) -> str:
        """Clean the LLM debate response."""
        # First remove thinking tags and artifacts
        response = clean_llm_response(response)

        # No character limit - show full message
        response = response.strip()

        # If response is empty or just whitespace after cleaning, provide fallback
        if not response or len(response) < 3:
            return "Estoy analizando la situacion..."

        return response

    def _clean_vote_response(self, response: str, valid_names: list[str]) -> str:
        """Clean the LLM vote response and extract player name."""
        # First remove thinking tags and artifacts
        response = clean_llm_response(response)
        response = response.strip().lower()

        # First try: look for exact player name anywhere in response
        for name in valid_names:
            if name.lower() in response:
                return name

        # Second try: remove common prefixes and take first word
        for prefix in ["voto por ", "mi voto es ", "elijo a ", "voto: ", "mi voto: ", "voto a "]:
            if response.startswith(prefix):
                response = response[len(prefix):]

        # Take first word and check if it matches any valid name
        first_word = response.split()[0] if response.split() else ""
        for name in valid_names:
            if name.lower().startswith(first_word) or first_word.startswith(name.lower()):
                return name

        return first_word if first_word else ""
# reload trigger
