"""
Assign Classic 10 rounds based on publish date chronology

Classic 10 YERR OUT format follows a pattern:
- Multiple Round-Robin games
- ONE Elimination game
- Repeat for next round

This script uses publish dates to group games and assign rounds.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
from src.config import DB_PATH
from datetime import datetime

def analyze_classic10_chronology():
    """
    Analyze Classic 10 games by publish date to identify round boundaries
    """
    db = DatabaseManager(DB_PATH)

    with db.get_connection() as conn:
        # Get all Classic 10 games with publish dates, ordered chronologically
        cursor = conn.execute("""
            SELECT
                gr.video_id,
                v.title,
                v.published_at,
                gr.game_type,
                gr.player_a,
                gr.player_b,
                gr.winner
            FROM game_results gr
            JOIN videos v ON gr.video_id = v.video_id
            WHERE gr.game_type LIKE '%Classic 10%'
            ORDER BY v.published_at
        """)
        games = cursor.fetchall()

    print("="*80)
    print("CLASSIC 10 CHRONOLOGICAL ANALYSIS")
    print("="*80)
    print(f"\nTotal Classic 10 games: {len(games)}\n")

    # Group games and identify elimination games
    for i, game in enumerate(games, 1):
        game_type = game['game_type'] or 'Unknown'
        is_elimination = 'elimination' in game_type.lower()
        has_round = any(f'round {r}' in game_type.lower() for r in [1, 2, 3, 4])

        # Format display
        marker = ""
        if is_elimination:
            marker = " [ELIM]"
        elif not has_round and 'classic 10' in game_type.lower() and game_type.lower().strip() != 'classic 10':
            marker = " [TAGGED]"
        elif game_type.lower().strip() == 'classic 10':
            marker = " [UNTAGGED]"

        print(f"{i:2}. {game['published_at'][:10]} | {game['player_a']:25} vs {game['player_b']:25}{marker}")
        if game_type != 'Unknown':
            print(f"    Type: {game_type}")
        print()

    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80)

    # Try to identify round boundaries based on elimination games
    elimination_indices = []
    for i, game in enumerate(games):
        game_type = game['game_type'] or ''
        if 'elimination' in game_type.lower():
            elimination_indices.append(i)
            print(f"Elimination game #{i+1}: {game['published_at'][:10]} - {game['player_a']} vs {game['player_b']}")

    print(f"\nFound {len(elimination_indices)} elimination games")
    print("\nSuggested round boundaries:")

    # Propose round assignments
    if len(elimination_indices) > 0:
        print(f"  Round 1: Games 1-{elimination_indices[0]+1}")
    if len(elimination_indices) > 1:
        print(f"  Round 2: Games {elimination_indices[0]+2}-{elimination_indices[1]+1}")
    if len(elimination_indices) > 2:
        print(f"  Round 3: Games {elimination_indices[1]+2}-{elimination_indices[2]+1}")
    if len(elimination_indices) > 3:
        print(f"  Finals: Games {elimination_indices[2]+2}-{len(games)}")
    elif len(elimination_indices) == 3:
        print(f"  Finals: Games {elimination_indices[2]+2}-{len(games)}")

    return games, elimination_indices


def suggest_round_assignments():
    """
    Suggest specific SQL updates to assign rounds based on chronology
    """
    games, elim_indices = analyze_classic10_chronology()

    print("\n" + "="*80)
    print("SUGGESTED UPDATES")
    print("="*80)

    if len(elim_indices) < 3:
        print("\nWARNING: Less than 3 elimination games found!")
        print("Classic 10 should have at least 3 elimination games (one per round)")
        print("Manual review recommended.")
        return

    # Build suggested assignments
    round_assignments = []

    # Round 1: Start to first elimination
    round_1_games = games[:elim_indices[0]+1]

    # Round 2: After first elim to second elim
    round_2_games = games[elim_indices[0]+1:elim_indices[1]+1]

    # Round 3: After second elim to third elim
    round_3_games = games[elim_indices[1]+1:elim_indices[2]+1]

    # Finals: After third elim to end
    finals_games = games[elim_indices[2]+1:]

    print("\nRound 1 assignments:")
    for game in round_1_games:
        game_type = game['game_type'] or ''
        is_elim = 'elimination' in game_type.lower()
        new_type = "Classic 10 - Round 1 - Elimination" if is_elim else "Classic 10 - Round 1 - Round Robin"

        # Only show if needs update
        if 'round 1' not in game_type.lower():
            print(f"  {game['video_id']}: {game['title'][:50]}")
            print(f"    Current: {game_type}")
            print(f"    Suggest: {new_type}")
            round_assignments.append((game['video_id'], new_type))

    print("\nRound 2 assignments:")
    for game in round_2_games:
        game_type = game['game_type'] or ''
        is_elim = 'elimination' in game_type.lower()
        new_type = "Classic 10 - Round 2 - Elimination" if is_elim else "Classic 10 - Round 2 - Round Robin"

        if 'round 2' not in game_type.lower():
            print(f"  {game['video_id']}: {game['title'][:50]}")
            print(f"    Current: {game_type}")
            print(f"    Suggest: {new_type}")
            round_assignments.append((game['video_id'], new_type))

    print("\nRound 3 assignments:")
    for game in round_3_games:
        game_type = game['game_type'] or ''
        is_elim = 'elimination' in game_type.lower()
        new_type = "Classic 10 - Round 3 - Elimination" if is_elim else "Classic 10 - Round 3 - Round Robin"

        if 'round 3' not in game_type.lower():
            print(f"  {game['video_id']}: {game['title'][:50]}")
            print(f"    Current: {game_type}")
            print(f"    Suggest: {new_type}")
            round_assignments.append((game['video_id'], new_type))

    print("\nFinals assignments:")
    for game in finals_games:
        game_type = game['game_type'] or ''
        is_elim = 'elimination' in game_type.lower()
        new_type = "Classic 10 - Finals - Championship" if is_elim else "Classic 10 - Finals"

        if 'finals' not in game_type.lower() and 'final' not in game_type.lower():
            print(f"  {game['video_id']}: {game['title'][:50]}")
            print(f"    Current: {game_type}")
            print(f"    Suggest: {new_type}")
            round_assignments.append((game['video_id'], new_type))

    print(f"\n\nTotal updates suggested: {len(round_assignments)}")

    # Ask for confirmation
    if round_assignments:
        print("\n" + "="*80)
        response = input("Apply these updates? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            apply_updates(round_assignments)
        else:
            print("Updates cancelled.")


def apply_updates(assignments):
    """
    Apply the round assignments to the database
    """
    db = DatabaseManager(DB_PATH)

    print("\nApplying updates...")

    with db.get_connection() as conn:
        for video_id, new_game_type in assignments:
            conn.execute("""
                UPDATE game_results
                SET game_type = ?
                WHERE video_id = ?
            """, (new_game_type, video_id))
            print(f"  Updated {video_id} -> {new_game_type}")

        conn.commit()

    print(f"\n✓ Successfully updated {len(assignments)} games")
    print("\nRun 'python webapp/generate_static_site.py' to regenerate the website with updated data")


if __name__ == '__main__':
    suggest_round_assignments()
