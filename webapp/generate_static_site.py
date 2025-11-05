"""
Generate static HTML site with embedded stats data
Run this script whenever you want to publish updated stats
"""

import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp.backend.stats_calculator import StatsCalculator
from webapp.backend.processing_stats import ProcessingStats

def generate_static_site():
    """Generate static HTML with embedded data"""

    print("Generating static site with latest stats...")

    # Get all the data - use absolute path to database
    # Get the project root (go up from webapp/ to DingerStats/)
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(webapp_dir)
    db_path = os.path.join(project_root, 'database', 'dingerstats.db')
    print(f"  Using database: {db_path}")
    calc = StatsCalculator(db_path=db_path)
    proc_stats = ProcessingStats(db_path=db_path)

    players = calc.get_all_players()
    standings = calc.get_player_records()
    game_types = calc.get_game_types()
    all_games = calc.db.get_all_game_results()  # Get ALL games for h2h
    recent_games = all_games[:20] if all_games else []  # Show 20 most recent
    processing_stats = proc_stats.get_stats()

    print(f"  Found {len(players)} players")
    print(f"  Found {len(standings)} standings entries")
    print(f"  Found {len(all_games)} total games")

    # Read the 2005-style template
    template_path = os.path.join(os.path.dirname(__file__), 'frontend', 'index_template_2005.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Prepare data as JSON
    data = {
        'players': players,
        'standings': standings,
        'game_types': game_types,
        'recent_games': all_games,  # Include ALL games for h2h filtering, frontend will show first 20
        'processing_stats': processing_stats
    }

    # Inject data into HTML
    data_json = json.dumps(data, indent=2)
    html = html.replace('/* DATA_PLACEHOLDER */', f'const STATS_DATA = {data_json};')

    # Write output
    output_path = os.path.join(os.path.dirname(__file__), 'frontend', 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nStatic site generated: {output_path}")
    print("Ready to deploy to Vercel!")

if __name__ == '__main__':
    generate_static_site()
