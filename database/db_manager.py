"""
Database Manager for DingerStats
Handles SQLite database operations for video metadata and game results
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str = "database/dingerstats.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.ensure_database_exists()

    def ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Read schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema = f.read()

        # Create tables
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)
            conn.commit()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    # ==================== VIDEO OPERATIONS ====================

    def insert_video(self, video_data: Dict) -> bool:
        """Insert or update video metadata"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO videos
                    (video_id, title, description, published_at, channel_id,
                     playlist_id, duration, thumbnail_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_data['video_id'],
                    video_data.get('title', ''),
                    video_data.get('description', ''),
                    video_data.get('published_at', ''),
                    video_data.get('channel_id', ''),
                    video_data.get('playlist_id', ''),
                    video_data.get('duration', ''),
                    video_data.get('thumbnail_url', '')
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting video {video_data.get('video_id')}: {e}")
            return False

    def batch_insert_videos(self, videos: List[Dict]) -> int:
        """Batch insert multiple videos"""
        success_count = 0
        for video in videos:
            if self.insert_video(video):
                success_count += 1
        return success_count

    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get video by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM videos WHERE video_id = ?", (video_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_videos(self) -> List[Dict]:
        """Get all videos"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM videos ORDER BY published_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_videos_by_playlist(self, playlist_id: str) -> List[Dict]:
        """Get all videos from a specific playlist"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM videos WHERE playlist_id = ? ORDER BY published_at DESC",
                (playlist_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== GAME RESULTS OPERATIONS ====================

    def insert_game_result(self, result_data: Dict) -> bool:
        """Insert game analysis result"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_results
                    (video_id, player_a, player_b, team_a, team_b, score_a, score_b, winner,
                     raw_response, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_data['video_id'],
                    result_data.get('player_a'),
                    result_data.get('player_b'),
                    result_data.get('team_a'),
                    result_data.get('team_b'),
                    result_data.get('score_a'),
                    result_data.get('score_b'),
                    result_data.get('winner'),
                    result_data.get('raw_response'),
                    result_data.get('confidence', 'medium')
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting game result for {result_data.get('video_id')}: {e}")
            return False

    def get_game_result(self, video_id: str) -> Optional[Dict]:
        """Get game result for a video"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM game_results WHERE video_id = ? ORDER BY analyzed_at DESC LIMIT 1",
                (video_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_game_results(self) -> List[Dict]:
        """Get all game results"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT gr.*, v.title, v.published_at
                FROM game_results gr
                JOIN videos v ON gr.video_id = v.video_id
                ORDER BY gr.analyzed_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== PROCESSING LOG OPERATIONS ====================

    def update_processing_status(self, video_id: str, status: str,
                                  error_message: str = None) -> bool:
        """Update processing status for a video"""
        try:
            with self.get_connection() as conn:
                # Check if record exists
                cursor = conn.execute(
                    "SELECT attempt_count FROM processing_log WHERE video_id = ?",
                    (video_id,)
                )
                row = cursor.fetchone()

                if row:
                    # Update existing
                    attempt_count = row['attempt_count'] + 1
                    conn.execute("""
                        UPDATE processing_log
                        SET status = ?, error_message = ?, attempt_count = ?,
                            last_attempt = CURRENT_TIMESTAMP
                        WHERE video_id = ?
                    """, (status, error_message, attempt_count, video_id))
                else:
                    # Insert new
                    conn.execute("""
                        INSERT INTO processing_log (video_id, status, error_message, attempt_count)
                        VALUES (?, ?, ?, 1)
                    """, (video_id, status, error_message))

                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating processing status for {video_id}: {e}")
            return False

    def get_videos_by_status(self, status: str) -> List[Dict]:
        """Get all videos with a specific processing status"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT v.*, pl.status, pl.last_attempt, pl.attempt_count
                FROM videos v
                LEFT JOIN processing_log pl ON v.video_id = pl.video_id
                WHERE pl.status = ?
                ORDER BY pl.last_attempt DESC
            """, (status,))
            return [dict(row) for row in cursor.fetchall()]

    def get_unprocessed_videos(self) -> List[Dict]:
        """Get videos that haven't been analyzed yet"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT v.* FROM videos v
                LEFT JOIN processing_log pl ON v.video_id = pl.video_id
                WHERE pl.video_id IS NULL OR pl.status = 'failed'
                ORDER BY v.published_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== STATS & UTILITIES ====================

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}

            # Total videos
            cursor = conn.execute("SELECT COUNT(*) as count FROM videos")
            stats['total_videos'] = cursor.fetchone()['count']

            # Total analyzed
            cursor = conn.execute("SELECT COUNT(DISTINCT video_id) as count FROM game_results")
            stats['analyzed_videos'] = cursor.fetchone()['count']

            # By status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM processing_log
                GROUP BY status
            """)
            stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

            return stats

    def clear_all_data(self):
        """Clear all data from database (use with caution!)"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM processing_log")
            conn.execute("DELETE FROM game_results")
            conn.execute("DELETE FROM videos")
            conn.commit()
