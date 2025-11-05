"""
Stats Calculator for DingerStats
Calculates player records, head-to-head, and other stats from the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
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
            player_a = result.get('player_a')
            player_b = result.get('player_b')
            winner = result.get('winner')

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

        for result in all_results:
            player_a = result.get('player_a')
            player_b = result.get('player_b')
            winner = result.get('winner')

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
                players.add(result.get('player_a'))
            if result.get('player_b'):
                players.add(result.get('player_b'))

        return sorted(list(players))

    def get_recent_games(self, limit=10):
        """Get most recent games"""
        all_results = self.db.get_all_game_results()

        games = []
        for result in all_results[:limit]:
            games.append({
                'player_a': result.get('player_a'),
                'player_b': result.get('player_b'),
                'score_a': result.get('score_a'),
                'score_b': result.get('score_b'),
                'winner': result.get('winner'),
                'game_type': result.get('game_type'),
                'video_title': result.get('title'),
                'date': result.get('published_at')
            })

        return games

    def get_game_types(self):
        """Get list of all unique game types"""
        all_results = self.db.get_all_game_results()

        types = set()
        for result in all_results:
            game_type = result.get('game_type')
            if game_type:
                types.add(game_type)

        return sorted(list(types))


if __name__ == "__main__":
    # Test the calculator
    calc = StatsCalculator()

    print("Player Standings:")
    standings = calc.get_player_records()
    for player in standings:
        print(f"  {player['player']}: {player['wins']}-{player['losses']} ({player['win_pct']:.3f})")
