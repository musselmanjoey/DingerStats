"""
DingerStats Debug UI
Simple terminal UI for inspecting database contents, prompt versions, and data quality
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.db_manager import DatabaseManager
from src.utils.player_normalizer import normalize_player_name
from src.utils.game_type_normalizer import normalize_game_type

def print_header(title):
    """Print a fancy header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def show_video_coverage():
    """Show which videos have been analyzed"""
    print_header("VIDEO COVERAGE")

    db = DatabaseManager()

    # Get all videos
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                v.playlist_id,
                COUNT(v.video_id) as total_videos,
                COUNT(gr.video_id) as analyzed_videos
            FROM videos v
            LEFT JOIN game_results gr ON v.video_id = gr.video_id
            GROUP BY v.playlist_id
        """)
        playlists = cursor.fetchall()

    print("\nPlaylist Coverage:")
    for playlist in playlists:
        playlist_id = playlist['playlist_id']
        total = playlist['total_videos']
        analyzed = playlist['analyzed_videos']
        pct = (analyzed / total * 100) if total > 0 else 0

        # Determine playlist name
        if 'x2Thksr' in playlist_id:
            name = "Classic 10"
        elif 'lmNdN4W' in playlist_id:
            name = "Season 10"
        else:
            name = playlist_id[:12]

        print(f"  {name:15} {analyzed:3}/{total:3} videos ({pct:5.1f}%)")

def show_prompt_versions():
    """Show distribution of prompt versions"""
    print_header("PROMPT VERSION DISTRIBUTION")

    db = DatabaseManager()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                prompt_version,
                COUNT(*) as count
            FROM game_results
            GROUP BY prompt_version
            ORDER BY prompt_version
        """)
        versions = cursor.fetchall()

    print("\nPrompt Versions:")
    for version in versions:
        ver = version['prompt_version'] or 'unknown'
        count = version['count']
        print(f"  {ver:10} {count:3} games")

def show_game_types():
    """Show game type distribution"""
    print_header("GAME TYPE DISTRIBUTION")

    db = DatabaseManager()

    with db.get_connection() as conn:
        # Raw game types
        cursor = conn.execute("""
            SELECT
                prompt_version,
                game_type,
                COUNT(*) as count
            FROM game_results
            GROUP BY prompt_version, game_type
            ORDER BY prompt_version, count DESC
        """)
        results = cursor.fetchall()

    current_version = None
    for row in results:
        version = row['prompt_version'] or 'unknown'
        game_type = row['game_type'] or 'Unknown'
        count = row['count']

        if version != current_version:
            print(f"\n{version.upper()}:")
            current_version = version

        # Normalize for display
        normalized = normalize_game_type(game_type)
        print(f"  {count:3}x  {game_type:45} -> {normalized}")

def show_player_stats():
    """Show player statistics"""
    print_header("PLAYER STATISTICS")

    db = DatabaseManager()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                player_a as player,
                COUNT(*) as games_played,
                SUM(CASE WHEN winner = player_a THEN 1 ELSE 0 END) as wins
            FROM game_results
            WHERE player_a IS NOT NULL
            UNION ALL
            SELECT
                player_b as player,
                COUNT(*) as games_played,
                SUM(CASE WHEN winner = player_b THEN 1 ELSE 0 END) as wins
            FROM game_results
            WHERE player_b IS NOT NULL
        """)
        results = cursor.fetchall()

    # Aggregate by player
    player_stats = {}
    for row in results:
        player = normalize_player_name(row['player'])
        if player not in player_stats:
            player_stats[player] = {'games': 0, 'wins': 0}
        player_stats[player]['games'] += row['games_played']
        player_stats[player]['wins'] += row['wins']

    # Sort by games played
    sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['games'], reverse=True)

    print("\n{:30} {:>10} {:>10} {:>10}".format("Player", "Games", "Wins", "Win %"))
    print("-"*70)
    for player, stats in sorted_players:
        games = stats['games']
        wins = stats['wins']
        win_pct = (wins / games * 100) if games > 0 else 0
        print(f"{player:30} {games:10} {wins:10} {win_pct:9.1f}%")

def show_recent_games(limit=10):
    """Show recent game results"""
    print_header(f"RECENT {limit} GAMES")

    db = DatabaseManager()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                gr.player_a,
                gr.player_b,
                gr.score_a,
                gr.score_b,
                gr.winner,
                gr.game_type,
                gr.prompt_version,
                v.title,
                gr.analyzed_at
            FROM game_results gr
            JOIN videos v ON gr.video_id = v.video_id
            ORDER BY gr.analyzed_at DESC
            LIMIT ?
        """, (limit,))
        games = cursor.fetchall()

    print()
    for i, game in enumerate(games, 1):
        player_a = normalize_player_name(game['player_a']) or 'Unknown'
        player_b = normalize_player_name(game['player_b']) or 'Unknown'
        winner = normalize_player_name(game['winner']) or 'Unknown'
        game_type = normalize_game_type(game['game_type']) or 'Unknown'
        prompt_ver = game['prompt_version'] or 'v1'

        print(f"{i:2}. {player_a:20} vs {player_b:20}")
        print(f"    Score: {game['score_a'] or '?'}-{game['score_b'] or '?'}  Winner: {winner}")
        print(f"    Type: {game_type} (prompt: {prompt_ver})")
        print(f"    {game['title'][:60]}")
        print()

def show_menu():
    """Show interactive menu"""
    while True:
        print_header("DINGERSTATS DEBUG UI")
        print("\n1. Video Coverage")
        print("2. Prompt Versions")
        print("3. Game Types")
        print("4. Player Stats")
        print("5. Recent Games")
        print("6. Show All")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            show_video_coverage()
        elif choice == '2':
            show_prompt_versions()
        elif choice == '3':
            show_game_types()
        elif choice == '4':
            show_player_stats()
        elif choice == '5':
            num = input("How many recent games? (default 10): ").strip()
            limit = int(num) if num.isdigit() else 10
            show_recent_games(limit)
        elif choice == '6':
            show_video_coverage()
            show_prompt_versions()
            show_game_types()
            show_player_stats()
            show_recent_games()
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice!")

        input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
