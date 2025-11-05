"""
Generate Classic 10 page with sliding door round-by-round breakdown
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_manager import DatabaseManager
from src.utils.player_normalizer import normalize_player_name
from src.utils.game_type_normalizer import normalize_game_type
from collections import defaultdict

def parse_round_from_game_type(game_type):
    """Extract round number from game type like 'Classic 10 - Round 1 - Elimination'"""
    if not game_type:
        return None

    game_type_lower = game_type.lower()

    if 'finals' in game_type_lower or 'final' in game_type_lower:
        return 'Finals'

    if 'round 1' in game_type_lower:
        return 'Round 1'
    elif 'round 2' in game_type_lower:
        return 'Round 2'
    elif 'round 3' in game_type_lower:
        return 'Round 3'
    elif 'round 4' in game_type_lower:
        return 'Round 4'

    return None

def is_elimination_game(game_type):
    """Check if game is an elimination game"""
    if not game_type:
        return False
    return 'elimination' in game_type.lower()

def get_classic10_rounds():
    """Get Classic 10 games organized by round"""
    db = DatabaseManager()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                player_a, player_b, score_a, score_b, winner, game_type
            FROM game_results
            WHERE game_type LIKE '%Classic 10%'
            ORDER BY analyzed_at
        """)
        games = cursor.fetchall()

    # Organize by round
    rounds = defaultdict(lambda: {
        'round_robin': [],
        'elimination': None
    })

    for game in games:
        round_name = parse_round_from_game_type(game['game_type'])
        if not round_name:
            continue

        game_data = {
            'player_a': normalize_player_name(game['player_a']),
            'player_b': normalize_player_name(game['player_b']),
            'score_a': game['score_a'],
            'score_b': game['score_b'],
            'winner': normalize_player_name(game['winner']),
            'game_type': game['game_type']
        }

        if is_elimination_game(game['game_type']):
            rounds[round_name]['elimination'] = game_data
        else:
            rounds[round_name]['round_robin'].append(game_data)

    return dict(rounds)

def calculate_round_standings(round_games):
    """Calculate win-loss records for a round"""
    standings = defaultdict(lambda: {'wins': 0, 'losses': 0})

    for game in round_games:
        player_a = game['player_a']
        player_b = game['player_b']
        winner = game['winner']

        if winner == player_a:
            standings[player_a]['wins'] += 1
            standings[player_b]['losses'] += 1
        elif winner == player_b:
            standings[player_b]['wins'] += 1
            standings[player_a]['losses'] += 1

    # Sort by wins descending
    sorted_standings = sorted(standings.items(), key=lambda x: (x[1]['wins'], -x[1]['losses']), reverse=True)
    return sorted_standings

print("Generating Classic 10 rounds data...")
rounds = get_classic10_rounds()

print(f"Found {len(rounds)} rounds")
for round_name in sorted(rounds.keys()):
    round_data = rounds[round_name]
    print(f"  {round_name}: {len(round_data['round_robin'])} round-robin games, elimination: {round_data['elimination'] is not None}")

print("\nRounds data ready for HTML generation!")
print("Next: Update generate_tournament_pages.py to include this sliding door UI")
