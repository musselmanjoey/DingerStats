"""
Stats Calculator for DingerStats
Calculates player records, head-to-head, and other stats from the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
from src.utils.player_normalizer import normalize_player_name
from src.utils.game_type_normalizer import normalize_game_type, get_season_from_game_type, get_phase_from_game_type
from collections import defaultdict


class StatsCalculator:
    def __init__(self, db_path="../../database/dingerstats.db"):
        self.db = DatabaseManager(db_path)

    def get_player_records(self, game_type=None):
        """
        Calculate win-loss records for all players

        Args:
            game_type: Filter by game type (e.g., "Playoff", "Regular Season", etc.)

        Returns:
            List of player stats dicts sorted by wins
        """
        all_results = self.db.get_all_game_results()

        # Filter by game type if specified
        if game_type:
            all_results = [r for r in all_results if r.get('game_type') == game_type]

        player_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0})

        for result in all_results:
            player_a = normalize_player_name(result.get('player_a'))
            player_b = normalize_player_name(result.get('player_b'))
            winner = normalize_player_name(result.get('winner'))

            if not all([player_a, player_b, winner]):
                continue

            # Track games played
            player_stats[player_a]['games'] += 1
            player_stats[player_b]['games'] += 1

            # Track wins/losses
            if winner == player_a:
                player_stats[player_a]['wins'] += 1
                player_stats[player_b]['losses'] += 1
            elif winner == player_b:
                player_stats[player_b]['wins'] += 1
                player_stats[player_a]['losses'] += 1

        # Convert to list and calculate win percentage
        standings = []
        for player, stats in player_stats.items():
            win_pct = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            standings.append({
                'player': player,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'games': stats['games'],
                'win_pct': round(win_pct, 3)
            })

        # Sort by wins (desc), then win_pct (desc)
        standings.sort(key=lambda x: (x['wins'], x['win_pct']), reverse=True)

        return standings

    def get_head_to_head(self, player1, player2):
        """
        Get head-to-head record between two players

        Returns:
            Dict with matchup stats and game history
        """
        all_results = self.db.get_all_game_results()

        matchups = []
        player1_wins = 0
        player2_wins = 0

        # Normalize the input player names for comparison
        player1 = normalize_player_name(player1)
        player2 = normalize_player_name(player2)

        for result in all_results:
            player_a = normalize_player_name(result.get('player_a'))
            player_b = normalize_player_name(result.get('player_b'))
            winner = normalize_player_name(result.get('winner'))

            # Check if this game involves both players
            is_matchup = (
                (player_a == player1 and player_b == player2) or
                (player_a == player2 and player_b == player1)
            )

            if not is_matchup:
                continue

            # Track wins
            if winner == player1:
                player1_wins += 1
            elif winner == player2:
                player2_wins += 1

            # Add to matchups list
            matchups.append({
                'player_a': player_a,
                'player_b': player_b,
                'score_a': result.get('score_a'),
                'score_b': result.get('score_b'),
                'winner': winner,
                'game_type': result.get('game_type'),
                'video_title': result.get('title'),
                'date': result.get('published_at')
            })

        return {
            'player1': player1,
            'player2': player2,
            'player1_wins': player1_wins,
            'player2_wins': player2_wins,
            'total_games': len(matchups),
            'games': matchups
        }

    def get_all_players(self):
        """Get list of all unique players"""
        all_results = self.db.get_all_game_results()

        players = set()
        for result in all_results:
            if result.get('player_a'):
                players.add(normalize_player_name(result.get('player_a')))
            if result.get('player_b'):
                players.add(normalize_player_name(result.get('player_b')))

        return sorted(list(players))

    def get_recent_games(self, limit=10):
        """Get most recent games"""
        all_results = self.db.get_all_game_results()

        games = []
        for result in all_results[:limit]:
            games.append({
                'player_a': normalize_player_name(result.get('player_a')),
                'player_b': normalize_player_name(result.get('player_b')),
                'score_a': result.get('score_a'),
                'score_b': result.get('score_b'),
                'winner': normalize_player_name(result.get('winner')),
                'game_type': result.get('game_type'),
                'video_title': result.get('title'),
                'date': result.get('published_at')
            })

        return games

    def get_game_types(self):
        """Get list of all unique game types (normalized)"""
        all_results = self.db.get_all_game_results()

        types = set()
        for result in all_results:
            game_type = result.get('game_type')
            if game_type:
                normalized = normalize_game_type(game_type)
                types.add(normalized)

        return sorted(list(types))

    def get_seasons(self):
        """Get list of all unique seasons"""
        all_results = self.db.get_all_game_results()

        seasons = set()
        for result in all_results:
            game_type = result.get('game_type')
            if game_type:
                season = get_season_from_game_type(game_type)
                seasons.add(season)

        return sorted(list(seasons))

    def get_games_by_season(self, season_filter=None):
        """
        Get all games organized by season and phase

        Args:
            season_filter: Optional season to filter by (e.g., "Classic 10")

        Returns:
            Dict with structure:
            {
                'Classic 10': {
                    'Regular Season': [games...],
                    'Playoffs': [games...],
                    'Finals': [games...]
                }
            }
        """
        all_results = self.db.get_all_game_results()

        organized = defaultdict(lambda: defaultdict(list))

        for result in all_results:
            game_type = result.get('game_type')
            season = get_season_from_game_type(game_type)
            phase = get_phase_from_game_type(game_type)

            # Skip if filtering by season and this doesn't match
            if season_filter and season != season_filter:
                continue

            game_data = {
                'player_a': normalize_player_name(result.get('player_a')),
                'player_b': normalize_player_name(result.get('player_b')),
                'score_a': result.get('score_a'),
                'score_b': result.get('score_b'),
                'winner': normalize_player_name(result.get('winner')),
                'game_type': normalize_game_type(game_type),
                'video_id': result.get('video_id'),
                'video_title': result.get('title'),
                'date': result.get('published_at')
            }

            organized[season][phase].append(game_data)

        return dict(organized)


if __name__ == "__main__":
    # Test the calculator
    calc = StatsCalculator()

    print("Player Standings:")
    standings = calc.get_player_records()
    for player in standings:
        print(f"  {player['player']}: {player['wins']}-{player['losses']} ({player['win_pct']:.3f})")
