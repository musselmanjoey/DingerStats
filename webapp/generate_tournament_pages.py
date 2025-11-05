"""
Generate static tournament HTML pages for each season
Run this script whenever you want to publish updated tournament pages
"""

import json
import sys
import os
from collections import defaultdict

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp.backend.stats_calculator import StatsCalculator
from database.db_manager import DatabaseManager
from src.utils.player_normalizer import normalize_player_name

def parse_round_from_game_type(game_type):
    """Extract round number from game type like 'Classic 10 - Round 1 - Elimination'"""
    if not game_type:
        return None

    game_type_lower = game_type.lower()

    # Check for Finals/Round 4 (treat Round 4 as Finals for Classic 10)
    if 'finals' in game_type_lower or 'final' in game_type_lower or 'round 4' in game_type_lower:
        return 'Finals'

    # Check for specific rounds
    if 'round 1' in game_type_lower:
        return 'Round 1'
    elif 'round 2' in game_type_lower:
        return 'Round 2'
    elif 'round 3' in game_type_lower:
        return 'Round 3'

    # Fallback: if it just says "Classic 10" or vague tournament format, skip it
    # We only want clearly tagged rounds
    return None

def is_elimination_game(game_type):
    """Check if game is an elimination game"""
    if not game_type:
        return False
    return 'elimination' in game_type.lower()

def get_classic10_rounds_data(db_path, analyzer_type=None, prompt_version=None):
    """Get Classic 10 games organized by round with standings"""
    db = DatabaseManager(db_path)

    # Build query with optional filters
    query = """
        SELECT
            player_a, player_b, score_a, score_b, winner, game_type
        FROM game_results
        WHERE game_type LIKE '%Classic 10%'
    """
    params = []

    if analyzer_type:
        query += " AND analyzer_type = ?"
        params.append(analyzer_type)

    if prompt_version:
        query += " AND prompt_version = ?"
        params.append(prompt_version)

    query += " ORDER BY analyzed_at"

    with db.get_connection() as conn:
        cursor = conn.execute(query, params)
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

    # Calculate standings for each round
    rounds_with_standings = {}
    for round_name, round_data in rounds.items():
        # Calculate standings from round-robin games
        standings = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for game in round_data['round_robin']:
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
        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]['wins'], -x[1]['losses']),
            reverse=True
        )

        rounds_with_standings[round_name] = {
            'round_robin': round_data['round_robin'],
            'elimination': round_data['elimination'],
            'standings': [{'player': p, 'wins': s['wins'], 'losses': s['losses']}
                         for p, s in sorted_standings]
        }

    return rounds_with_standings

def generate_tournament_page(season_name, season_data_multi_source, template_path, output_dir, db_path=None):
    """
    Generate a tournament page for a specific season

    Args:
        season_name: Name of the season (e.g., "Classic 10", "Season 10")
        season_data_multi_source: Dict with data keyed by source (e.g., {"gemini_v2": {...}, "ollama_v1": {...}})
        template_path: Path to HTML template
        output_dir: Directory to write output files
    """
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Get first available data source for placeholder values
    first_source_data = next(iter(season_data_multi_source.values()))

    # Calculate total games from first source
    total_games = sum(len(games) for games in first_source_data.values())

    # Replace common placeholders
    html = html.replace('TOURNAMENT_TITLE', season_name)
    html = html.replace('TOTAL_GAMES', str(total_games))

    # Replace format-specific placeholders (for Season template)
    if 'Regular Season' in first_source_data:
        regular_count = len(first_source_data.get('Regular Season', []))
        playoffs_count = len(first_source_data.get('Playoffs', []))
        finals_count = len(first_source_data.get('Finals', []))
        html = html.replace('REGULAR_SEASON_COUNT', str(regular_count))
        html = html.replace('PLAYOFFS_COUNT', str(playoffs_count))
        html = html.replace('FINALS_COUNT', str(finals_count))

    # Inject multi-source tournament data
    data_json = json.dumps(season_data_multi_source, indent=2)
    html = html.replace('/* TOURNAMENT_DATA_PLACEHOLDER */', f'window.TOURNAMENT_DATA_MULTI_SOURCE = {data_json};')

    # For Classic 10, also inject rounds data for sliding door UI (multi-source)
    if 'Classic' in season_name and 'Season' not in season_name and db_path:
        # Get rounds data for each source
        rounds_data_multi_source = {}
        for source_key in season_data_multi_source.keys():
            # Parse source key like "gemini_visual_v2" -> analyzer="gemini_visual", version="v2"
            parts = source_key.rsplit('_', 1)  # Split from right to get version
            if len(parts) == 2:
                analyzer = parts[0]
                version = parts[1]
                rounds_data_multi_source[source_key] = get_classic10_rounds_data(
                    db_path,
                    analyzer_type=analyzer,
                    prompt_version=version
                )

        rounds_json = json.dumps(rounds_data_multi_source, indent=2)
        html = html.replace('/* ROUNDS_DATA_PLACEHOLDER */', f'window.ROUNDS_DATA_MULTI_SOURCE = {rounds_json};')

    # Generate output filename (e.g., "Classic 10" -> "classic-10.html")
    filename = season_name.lower().replace(' ', '-') + '.html'
    output_path = os.path.join(output_dir, filename)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  [OK] Generated: {filename} ({total_games} games)")
    return output_path

def generate_all_tournament_pages():
    """Generate tournament pages for all seasons with multi-source data"""

    print("Generating tournament pages with multi-source data...")

    # Get data
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(webapp_dir)
    db_path = os.path.join(project_root, 'database', 'dingerstats.db')

    calc = StatsCalculator(db_path=db_path)

    # Get available data sources
    data_sources = calc.get_available_data_sources()
    print(f"  Available analyzers: {', '.join(data_sources['analyzer_types'])}")
    print(f"  Available prompt versions: {', '.join(data_sources['prompt_versions'])}")
    print(f"  Available combinations: {len(data_sources['combinations'])}")

    # Get all seasons
    all_seasons = calc.get_seasons()

    if not all_seasons:
        print("  No games found in database!")
        return

    # Output directory
    output_dir = os.path.join(webapp_dir, 'frontend')

    print(f"  Using database: {db_path}")
    print(f"  Found {len(all_seasons)} season(s)")

    generated_pages = []

    # Generate a page for each season
    for season_name in all_seasons:
        print(f"\n  Processing: {season_name}")

        # Get data for each analyzer + prompt version combination
        season_data_multi_source = {}

        for combo in data_sources['combinations']:
            analyzer = combo['analyzer']
            version = combo['version']
            source_key = f"{analyzer}_{version}"

            print(f"    Getting data for {source_key}... ", end='')

            # Get games for this specific combination and season
            games = calc.get_games_by_season(
                season_filter=season_name,
                analyzer_type=analyzer,
                prompt_version=version
            )

            # Only include if this source has data for this season
            if games and season_name in games:
                season_data_multi_source[source_key] = games[season_name]
                game_count = sum(len(g) for g in games[season_name].values())
                print(f"{game_count} games")
            else:
                print("no data")

        if not season_data_multi_source:
            print(f"    WARNING: No data for {season_name}, skipping")
            continue

        # Choose template based on season type
        if 'Classic' in season_name and 'Season' not in season_name:
            # Use Classic 10 YERR OUT! template
            template_path = os.path.join(webapp_dir, 'frontend', 'classic_10_template_2005.html')
        else:
            # Use standard Season template (Regular Season → Playoffs → Finals)
            template_path = os.path.join(webapp_dir, 'frontend', 'season_template_2005.html')

        output_path = generate_tournament_page(
            season_name=season_name,
            season_data_multi_source=season_data_multi_source,
            template_path=template_path,
            output_dir=output_dir,
            db_path=db_path
        )
        generated_pages.append({
            'name': season_name,
            'filename': os.path.basename(output_path),
            'path': output_path
        })

    print(f"\n[OK] Generated {len(generated_pages)} tournament page(s)")
    print("\nGenerated pages:")
    for page in generated_pages:
        print(f"  - {page['name']}: {page['filename']}")

    return generated_pages

if __name__ == '__main__':
    generate_all_tournament_pages()
