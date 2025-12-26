"""
Game export functionality - generates HTML reports of completed games.
"""
from datetime import datetime
from typing import Optional
from models.schemas import GameState, Player, DebateMessage, Vote


# Greek letter icons mapping
GREEK_ICONS = {
    'Alfa': '🅰️',
    'Beta': '🅱️',
    'Gamma': 'Γ',
    'Delta': 'Δ',
    'Epsilon': 'Ε',
    'Zeta': 'Ζ',
    'Sigma': 'Σ',
}


def get_player_icon(player: Player) -> str:
    """Get the icon for a player."""
    if player.is_human:
        return '👤'
    return GREEK_ICONS.get(player.display_name, '🤖')


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))


def generate_game_html(game: GameState, leaderboard: list = None) -> str:
    """
    Generate a complete HTML report of a game.

    Args:
        game: The completed game state
        leaderboard: Optional leaderboard data

    Returns:
        Complete HTML string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Find impostor
    impostor = next((p for p in game.players if p.is_impostor), None)
    impostor_name = impostor.display_name if impostor else "?"
    impostor_color = impostor.color if impostor else "#fff"

    # Determine winner
    winner_text = "🎉 ¡Inocentes Ganan!" if game.winner == "innocents" else "🎭 ¡Impostor Gana!"
    winner_class = "winner-innocents" if game.winner == "innocents" else "winner-impostor"

    # Generate sections
    players_html = _generate_players_section(game.players)
    words_html = _generate_words_section(game.players, game.impostor_id)
    debate_html = _generate_debate_section(game.debate_messages, game.players, game.impostor_id)
    votes_html = _generate_votes_section(game.votes, game.players)
    result_html = _generate_result_section(game, impostor)
    leaderboard_html = _generate_leaderboard_section(leaderboard) if leaderboard else ""

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Partida Impostor LLM - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e5e7eb;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            background: rgba(45, 45, 68, 0.8);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
        }}

        .header .timestamp {{
            color: #9ca3af;
            font-size: 0.9rem;
        }}

        .header .secret-word {{
            font-size: 1.5rem;
            color: #fbbf24;
            margin: 16px 0;
        }}

        .header .impostor-reveal {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(239, 68, 68, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .section {{
            background: rgba(31, 41, 55, 0.6);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }}

        .section h2 {{
            font-size: 1.25rem;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        /* Players */
        .players-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }}

        .player-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(55, 65, 81, 0.5);
            padding: 12px;
            border-radius: 8px;
        }}

        .player-icon {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}

        .player-info {{
            flex: 1;
        }}

        .player-name {{
            font-weight: 600;
        }}

        .player-model {{
            font-size: 0.75rem;
            color: #9ca3af;
        }}

        .player-impostor {{
            border: 2px solid #ef4444;
        }}

        /* Words */
        .words-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .word-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(55, 65, 81, 0.7);
            font-size: 0.9rem;
        }}

        .word-badge.impostor {{
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.4);
        }}

        /* Debate */
        .debate-messages {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .debate-message {{
            background: rgba(55, 65, 81, 0.5);
            border-radius: 8px;
            padding: 12px;
            border-left: 3px solid #22c55e;
        }}

        .debate-message.impostor {{
            border-left-color: #ef4444;
        }}

        .message-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }}

        .message-number {{
            background: rgba(0,0,0,0.3);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            color: #9ca3af;
        }}

        .message-role {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
        }}

        .role-impostor {{
            background: rgba(239, 68, 68, 0.3);
            color: #fca5a5;
        }}

        .role-innocent {{
            background: rgba(34, 197, 94, 0.3);
            color: #86efac;
        }}

        .message-content {{
            line-height: 1.5;
        }}

        /* Votes */
        .votes-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .vote-card {{
            background: rgba(55, 65, 81, 0.5);
            border-radius: 8px;
            padding: 12px;
        }}

        .vote-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .vote-arrow {{
            color: #9ca3af;
        }}

        .vote-justification {{
            margin-top: 8px;
            padding-left: 12px;
            border-left: 2px solid rgba(255,255,255,0.1);
            font-style: italic;
            color: #9ca3af;
            font-size: 0.9rem;
        }}

        /* Result */
        .result-banner {{
            text-align: center;
            padding: 32px;
            border-radius: 16px;
            margin-bottom: 20px;
        }}

        .winner-innocents {{
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.2));
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}

        .winner-impostor {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .result-banner h2 {{
            font-size: 2rem;
            margin-bottom: 16px;
            border: none;
            padding: 0;
        }}

        .result-detail {{
            color: #d1d5db;
            margin: 8px 0;
        }}

        .impostor-guess {{
            margin-top: 16px;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }}

        .guess-correct {{
            color: #22c55e;
        }}

        .guess-wrong {{
            color: #ef4444;
        }}

        /* Leaderboard */
        .leaderboard-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .leaderboard-table th,
        .leaderboard-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .leaderboard-table th {{
            color: #9ca3af;
            font-weight: 500;
        }}

        .leaderboard-rank {{
            font-size: 1.2rem;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 0.8rem;
        }}

        .footer a {{
            color: #60a5fa;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎭 Palabra Impostor</h1>
            <p class="timestamp">{timestamp}</p>
            <p class="secret-word">Palabra secreta: <strong>{escape_html(game.secret_word)}</strong></p>
            <div class="impostor-reveal">
                <span>Impostor:</span>
                <span style="color: {impostor_color}; font-weight: bold;">{escape_html(impostor_name)}</span>
            </div>
        </div>

        <!-- Result Banner -->
        <div class="result-banner {winner_class}">
            <h2>{winner_text}</h2>
            {result_html}
        </div>

        <!-- Players -->
        <div class="section">
            <h2>👥 Jugadores</h2>
            {players_html}
        </div>

        <!-- Words -->
        <div class="section">
            <h2>💬 Palabras Dichas</h2>
            {words_html}
        </div>

        <!-- Debate -->
        <div class="section">
            <h2>🗣️ Debate ({len(game.debate_messages)} mensajes)</h2>
            {debate_html}
        </div>

        <!-- Votes -->
        <div class="section">
            <h2>🗳️ Votación</h2>
            {votes_html}
        </div>

        {leaderboard_html}

        <!-- Footer -->
        <div class="footer">
            <p>Generado por <a href="https://github.com/your-repo/impostor-llm">Impostor LLM</a></p>
        </div>
    </div>
</body>
</html>'''

    return html


def _generate_players_section(players: list[Player]) -> str:
    """Generate the players grid HTML."""
    html_parts = ['<div class="players-grid">']

    for player in players:
        icon = get_player_icon(player)
        impostor_class = "player-impostor" if player.is_impostor else ""
        model_text = f"({player.model.split(':')[0]})" if player.model and player.model != 'human' else "(Humano)"

        html_parts.append(f'''
            <div class="player-card {impostor_class}">
                <div class="player-icon" style="background-color: {player.color}">
                    {icon}
                </div>
                <div class="player-info">
                    <div class="player-name" style="color: {player.color}">{escape_html(player.display_name)}</div>
                    <div class="player-model">{escape_html(model_text)}</div>
                </div>
            </div>
        ''')

    html_parts.append('</div>')
    return ''.join(html_parts)


def _generate_words_section(players: list[Player], impostor_id: str) -> str:
    """Generate the words list HTML."""
    html_parts = ['<div class="words-list">']

    for player in players:
        if player.words_said:
            is_impostor = player.id == impostor_id
            impostor_class = "impostor" if is_impostor else ""
            words = ", ".join(player.words_said)

            html_parts.append(f'''
                <div class="word-badge {impostor_class}">
                    <span style="color: {player.color}; font-weight: 600;">{escape_html(player.display_name)}:</span>
                    <span>{escape_html(words)}</span>
                </div>
            ''')

    html_parts.append('</div>')
    return ''.join(html_parts)


def _generate_debate_section(messages: list[DebateMessage], players: list[Player], impostor_id: str) -> str:
    """Generate the debate messages HTML."""
    if not messages:
        return '<p style="color: #9ca3af;">No hubo debate en esta partida.</p>'

    # Create player lookup
    player_map = {p.id: p for p in players}

    html_parts = ['<div class="debate-messages">']

    for i, msg in enumerate(messages, 1):
        player = player_map.get(msg.player_id)
        if not player:
            continue

        is_impostor = player.id == impostor_id
        impostor_class = "impostor" if is_impostor else ""
        role_class = "role-impostor" if is_impostor else "role-innocent"
        role_text = "Impostor" if is_impostor else "Inocente"

        html_parts.append(f'''
            <div class="debate-message {impostor_class}">
                <div class="message-header">
                    <span class="message-number">#{i}</span>
                    <span style="color: {player.color}; font-weight: 600;">{escape_html(player.display_name)}</span>
                    <span class="message-role {role_class}">{role_text}</span>
                </div>
                <div class="message-content">{escape_html(msg.message)}</div>
            </div>
        ''')

    html_parts.append('</div>')
    return ''.join(html_parts)


def _generate_votes_section(votes: list[Vote], players: list[Player]) -> str:
    """Generate the votes list HTML."""
    if not votes:
        return '<p style="color: #9ca3af;">No hubo votación en esta partida.</p>'

    # Create player lookup
    player_map = {p.id: p for p in players}

    html_parts = ['<div class="votes-list">']

    for vote in votes:
        voter = player_map.get(vote.voter_id)
        voted_for = player_map.get(vote.voted_for_id)

        if not voter or not voted_for:
            continue

        justification = vote.justification if hasattr(vote, 'justification') and vote.justification else ""

        html_parts.append(f'''
            <div class="vote-card">
                <div class="vote-header">
                    <span style="color: {voter.color}; font-weight: 600;">{escape_html(voter.display_name)}</span>
                    <span class="vote-arrow">→</span>
                    <span style="color: {voted_for.color}; font-weight: 600;">{escape_html(voted_for.display_name)}</span>
                </div>
                {f'<div class="vote-justification">"{escape_html(justification)}"</div>' if justification else ''}
            </div>
        ''')

    html_parts.append('</div>')
    return ''.join(html_parts)


def _generate_result_section(game: GameState, impostor: Optional[Player]) -> str:
    """Generate the result details HTML."""
    html_parts = []

    result_text = {
        'innocents_win': 'El impostor fue eliminado y no logró adivinar la palabra.',
        'impostor_wins_guess': '¡El impostor adivinó la palabra correcta!',
        'impostor_wins_hidden': 'El impostor no fue descubierto.'
    }

    if game.result:
        html_parts.append(f'<p class="result-detail">{result_text.get(game.result.value, "")}</p>')

    if game.impostor_guess:
        is_correct = game.result and game.result.value == 'impostor_wins_guess'
        guess_class = "guess-correct" if is_correct else "guess-wrong"
        guess_symbol = "✓" if is_correct else "✗"

        html_parts.append(f'''
            <div class="impostor-guess">
                <p>Adivinanza del impostor:</p>
                <p class="{guess_class}" style="font-size: 1.2rem; font-weight: bold;">
                    "{escape_html(game.impostor_guess)}" {guess_symbol}
                </p>
            </div>
        ''')

    return ''.join(html_parts)


def _generate_leaderboard_section(leaderboard: list) -> str:
    """Generate the leaderboard table HTML."""
    if not leaderboard:
        return ''

    html_parts = ['''
        <div class="section">
            <h2>🏆 Puntuaciones</h2>
            <table class="leaderboard-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Modelo</th>
                        <th>Victorias</th>
                        <th>Partidas</th>
                        <th>% Victoria</th>
                    </tr>
                </thead>
                <tbody>
    ''']

    rank_icons = ['🥇', '🥈', '🥉']

    for i, entry in enumerate(leaderboard[:10]):  # Top 10
        rank = rank_icons[i] if i < 3 else str(i + 1)
        win_rate = (entry.get('wins', 0) / entry.get('games', 1)) * 100 if entry.get('games', 0) > 0 else 0

        html_parts.append(f'''
            <tr>
                <td class="leaderboard-rank">{rank}</td>
                <td>{escape_html(entry.get('model', '?'))}</td>
                <td>{entry.get('wins', 0)}</td>
                <td>{entry.get('games', 0)}</td>
                <td>{win_rate:.1f}%</td>
            </tr>
        ''')

    html_parts.append('''
                </tbody>
            </table>
        </div>
    ''')

    return ''.join(html_parts)
