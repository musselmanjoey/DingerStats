"""
Flask API for DingerStats
Serves player stats, head-to-head data, and game results
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from stats_calculator import StatsCalculator

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize stats calculator
calc = StatsCalculator()


@app.route('/api/players', methods=['GET'])
def get_players():
    """Get list of all players"""
    try:
        players = calc.get_all_players()
        return jsonify({'players': players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/standings', methods=['GET'])
def get_standings():
    """Get player standings (win-loss records)"""
    try:
        game_type = request.args.get('game_type')
        standings = calc.get_player_records(game_type=game_type)
        return jsonify({'standings': standings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/head-to-head', methods=['GET'])
def get_head_to_head():
    """Get head-to-head matchup data"""
    try:
        player1 = request.args.get('player1')
        player2 = request.args.get('player2')

        if not player1 or not player2:
            return jsonify({'error': 'Missing player1 or player2 parameter'}), 400

        h2h = calc.get_head_to_head(player1, player2)
        return jsonify(h2h)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recent-games', methods=['GET'])
def get_recent_games():
    """Get recent games"""
    try:
        limit = request.args.get('limit', 10, type=int)
        games = calc.get_recent_games(limit=limit)
        return jsonify({'games': games})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/game-types', methods=['GET'])
def get_game_types():
    """Get all unique game types"""
    try:
        types = calc.get_game_types()
        return jsonify({'game_types': types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overview stats"""
    try:
        standings = calc.get_player_records()
        players = calc.get_all_players()
        game_types = calc.get_game_types()
        recent = calc.get_recent_games(limit=5)

        return jsonify({
            'total_players': len(players),
            'total_games': sum(p['games'] for p in standings) // 2 if standings else 0,
            'game_types': game_types,
            'recent_games': recent
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("DingerStats API Server")
    print("Access at: http://localhost:5000")
    print("")
    print("Endpoints:")
    print("  GET /api/players - List all players")
    print("  GET /api/standings - Player standings")
    print("  GET /api/standings?game_type=Playoff - Filter by game type")
    print("  GET /api/head-to-head?player1=Nick&player2=Dennis - Head to head")
    print("  GET /api/recent-games - Recent games")
    print("  GET /api/game-types - All game types")
    print("  GET /api/stats - Overview stats")
    print("")
    app.run(debug=True, port=5000)
