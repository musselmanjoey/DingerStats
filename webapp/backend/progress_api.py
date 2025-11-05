"""
Progress API for DingerStats
Shows real-time progress of video analysis
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Use absolute path to ensure we're reading the correct database
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../database/dingerstats.db'))
print(f"Using database at: {db_path}")
db = DatabaseManager(db_path=db_path)

# Playlist mappings
PLAYLISTS = {
    'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF': 'Classic 10',
    'PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2': 'Season 10',
}


@app.route('/api/progress')
def get_progress():
    """Get overall progress statistics"""

    with db.get_connection() as conn:
        # Get total videos per playlist
        cursor = conn.execute("""
            SELECT playlist_id, COUNT(*) as total
            FROM videos
            WHERE is_game = 1
            GROUP BY playlist_id
        """)
        playlist_totals = {row['playlist_id']: row['total'] for row in cursor.fetchall()}

        # Get analyzed counts by playlist and analyzer
        cursor = conn.execute("""
            SELECT
                v.playlist_id,
                gr.analyzer_type,
                gr.prompt_version,
                COUNT(DISTINCT gr.video_id) as analyzed,
                SUM(CASE WHEN gr.player_a IS NOT NULL THEN 1 ELSE 0 END) as successful
            FROM game_results gr
            JOIN videos v ON gr.video_id = v.video_id
            WHERE v.is_game = 1
            GROUP BY v.playlist_id, gr.analyzer_type, gr.prompt_version
        """)

        analyzed_stats = {}
        for row in cursor.fetchall():
            playlist = row['playlist_id']
            analyzer = row['analyzer_type']
            version = row['prompt_version']
            key = f"{playlist}_{analyzer}_{version}"

            analyzed_stats[key] = {
                'playlist': PLAYLISTS.get(playlist, playlist),
                'playlist_id': playlist,
                'analyzer': analyzer,
                'version': version,
                'total': playlist_totals.get(playlist, 0),
                'analyzed': row['analyzed'],
                'successful': row['successful'],
                'failed': row['analyzed'] - row['successful'],
                'remaining': playlist_totals.get(playlist, 0) - row['analyzed']
            }

        # Get recent activity (last 10 analyses)
        cursor = conn.execute("""
            SELECT
                v.title,
                v.video_id,
                gr.analyzer_type,
                gr.prompt_version,
                gr.player_a,
                gr.player_b,
                gr.winner,
                gr.analyzed_at
            FROM game_results gr
            JOIN videos v ON gr.video_id = v.video_id
            WHERE v.is_game = 1
            ORDER BY gr.analyzed_at DESC
            LIMIT 10
        """)

        recent_activity = []
        for row in cursor.fetchall():
            recent_activity.append({
                'title': row['title'],
                'video_id': row['video_id'],
                'analyzer': row['analyzer_type'],
                'version': row['prompt_version'],
                'success': row['player_a'] is not None,
                'players': f"{row['player_a']} vs {row['player_b']}" if row['player_a'] else "Failed",
                'winner': row['winner'],
                'timestamp': row['analyzed_at']
            })

    return jsonify({
        'stats': list(analyzed_stats.values()),
        'recent_activity': recent_activity
    })


@app.route('/')
def index():
    """Serve the progress dashboard"""
    return send_from_directory(app.static_folder, 'progress.html')


if __name__ == '__main__':
    print("Starting Progress Dashboard on http://localhost:5001")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5001, debug=True)
