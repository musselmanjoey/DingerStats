"""
Apply Classic 10 rounds based on chronological analysis

This script:
1. Gets all Classic 10 games by publish date
2. Removes duplicate video_ids (keeps first occurrence)
3. Identifies elimination games as round boundaries
4. Assigns rounds based on YERR OUT pattern
5. Applies updates to database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
from src.config import DB_PATH
from datetime import datetime

def is_grudge_match(title):
    """Check if video title suggests it's a grudge match or non-tournament game"""
    title_lower = title.lower()
    non_tournament_keywords = [
        'grudge match',
        'team swap',
        'revenge',
        'hitting is allowed',
        'big dog\'s revenge'
    ]
    return any(keyword in title_lower for keyword in non_tournament_keywords)

def get_clean_classic10_games():
    """Get Classic 10 games, removing duplicates and non-tournament games"""
    db = DatabaseManager(DB_PATH)

    with db.get_connection() as conn:
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
            ORDER BY v.published_at, gr.video_id
        """)
        all_games = cursor.fetchall()

    # Remove duplicates (keep first occurrence of each video_id)
    seen_video_ids = set()
    unique_games = []

    for game in all_games:
        if game['video_id'] not in seen_video_ids:
            # Skip grudge matches
            if not is_grudge_match(game['title']):
                seen_video_ids.add(game['video_id'])
                unique_games.append(game)
            else:
                print(f"  Skipping grudge match: {game['title'][:60]}")

    return unique_games

def identify_elimination_games(games):
    """Identify which games are elimination games"""
    elimination_indices = []

    for i, game in enumerate(games):
        game_type = game['game_type'] or ''
        if 'elimination' in game_type.lower():
            elimination_indices.append(i)

    return elimination_indices

def assign_rounds_by_chronology():
    """Assign rounds based on chronological order and elimination boundaries"""
    games = get_clean_classic10_games()

    print("=" * 80)
    print("CLASSIC 10 CHRONOLOGICAL ROUND ASSIGNMENT")
    print("=" * 80)
    print(f"\nTotal unique Classic 10 games: {len(games)}\n")

    # Identify elimination games
    elim_indices = identify_elimination_games(games)

    print(f"Found {len(elim_indices)} elimination games:")
    for idx in elim_indices:
        game = games[idx]
        print(f"  Game #{idx+1}: {game['published_at'][:10]} - {game['player_a']} vs {game['player_b']}")

    if len(elim_indices) < 3:
        print("\n⚠️  WARNING: Expected at least 3 elimination games for Classic 10 YERR OUT format")
        print("    Proceeding with available data...\n")

    # Determine round boundaries based on elimination games
    # Pattern: Round-Robin games → Elimination → next round

    assignments = []

    # Round 1: Start to first elimination (inclusive)
    if len(elim_indices) >= 1:
        round_1_end = elim_indices[0]
        for i in range(0, round_1_end + 1):
            game = games[i]
            is_elim = i == round_1_end
            new_type = "Classic 10 - Round 1 - Elimination" if is_elim else "Classic 10 - Round 1 - Round Robin"
            assignments.append((game['video_id'], new_type, game['title']))

    # Round 2: After first elim to second elim (inclusive)
    if len(elim_indices) >= 2:
        round_2_start = elim_indices[0] + 1
        round_2_end = elim_indices[1]
        for i in range(round_2_start, round_2_end + 1):
            game = games[i]
            is_elim = i == round_2_end
            new_type = "Classic 10 - Round 2 - Elimination" if is_elim else "Classic 10 - Round 2 - Round Robin"
            assignments.append((game['video_id'], new_type, game['title']))

    # Round 3: After second elim to third elim (inclusive)
    if len(elim_indices) >= 3:
        round_3_start = elim_indices[1] + 1
        round_3_end = elim_indices[2]
        for i in range(round_3_start, round_3_end + 1):
            game = games[i]
            is_elim = i == round_3_end
            new_type = "Classic 10 - Round 3 - Elimination" if is_elim else "Classic 10 - Round 3 - Round Robin"
            assignments.append((game['video_id'], new_type, game['title']))

    # Finals/Round 4: After third elim to end
    if len(elim_indices) >= 3:
        finals_start = elim_indices[2] + 1
        for i in range(finals_start, len(games)):
            game = games[i]
            # Check if there's a 4th elimination game
            is_elim = (len(elim_indices) >= 4 and i == elim_indices[3])
            new_type = "Classic 10 - Finals - Championship" if is_elim else "Classic 10 - Finals - Round Robin"
            assignments.append((game['video_id'], new_type, game['title']))

    # Display assignments by round
    print("\n" + "=" * 80)
    print("PROPOSED ROUND ASSIGNMENTS")
    print("=" * 80)

    current_round = None
    for video_id, new_type, title in assignments:
        round_name = new_type.split(' - ')[1] if ' - ' in new_type else 'Unknown'

        if round_name != current_round:
            current_round = round_name
            print(f"\n{current_round}:")

        print(f"  {video_id}: {title[:60]}")
        print(f"    -> {new_type}")

    print(f"\n\nTotal assignments: {len(assignments)}")

    return assignments

def apply_assignments(assignments):
    """Apply the round assignments to the database"""
    db = DatabaseManager(DB_PATH)

    print("\n" + "=" * 80)
    print("APPLYING UPDATES TO DATABASE")
    print("=" * 80)

    with db.get_connection() as conn:
        for video_id, new_game_type, title in assignments:
            conn.execute("""
                UPDATE game_results
                SET game_type = ?
                WHERE video_id = ?
            """, (new_game_type, video_id))
            print(f"  [OK] Updated: {video_id}")

        conn.commit()

    print(f"\n[SUCCESS] Successfully updated {len(assignments)} games")
    print("\nNext steps:")
    print("  1. Run 'python webapp/generate_tournament_pages.py' to regenerate tournament pages")
    print("  2. Review the classic-10.html page to verify round assignments")

if __name__ == '__main__':
    assignments = assign_rounds_by_chronology()

    if assignments:
        print("\n" + "=" * 80)
        print("Proceeding with updates...")
        apply_assignments(assignments)
    else:
        print("\n⚠️  No assignments to apply")
