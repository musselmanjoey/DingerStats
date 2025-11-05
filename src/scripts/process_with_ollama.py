"""
Process all Classic 10 videos with Ollama transcript analyzer
Runs in background while building the new UI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
from src.analyzers.ollama_transcript_analyzer import OllamaTranscriptAnalyzer


def process_all_videos():
    """Process all Classic 10 videos with Ollama"""

    # Initialize
    db = DatabaseManager()
    analyzer = OllamaTranscriptAnalyzer(model="llama3.2:3b")

    # Get all Classic 10 videos from the playlist
    CLASSIC_10_PLAYLIST = "PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF"

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT video_id, title, published_at
            FROM videos
            WHERE playlist_id = ? AND is_game = 1
            ORDER BY published_at
        """, (CLASSIC_10_PLAYLIST,))
        videos = cursor.fetchall()

    print("=" * 80)
    print("OLLAMA TRANSCRIPT ANALYSIS - CLASSIC 10")
    print("=" * 80)
    print(f"Total videos to process: {len(videos)}")
    print(f"Model: {analyzer.model}")
    print()

    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']

        print(f"[{i}/{len(videos)}] {title[:60]}")
        print(f"  Video ID: {video_id}")

        # Analyze
        result, raw_response = analyzer.analyze_game_video(video_id)

        if result:
            print(f"  SUCCESS:")
            print(f"    Players: {result.get('player_a')} vs {result.get('player_b')}")
            print(f"    Winner: {result.get('winner')}")
            print(f"    Score: {result.get('score_a')}-{result.get('score_b')}")
            print(f"    Confidence: {result.get('confidence')}")

            # Store in database with metadata
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_results
                    (video_id, player_a, player_b, team_a, team_b,
                     score_a, score_b, winner, game_type,
                     raw_response, analyzer_type, prompt_version, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_id,
                    result.get('player_a'),
                    result.get('player_b'),
                    result.get('player_a'),  # team_a same as player_a for now
                    result.get('player_b'),  # team_b same as player_b for now
                    result.get('score_a'),
                    result.get('score_b'),
                    result.get('winner'),
                    result.get('game_type'),
                    raw_response,
                    'ollama_transcript',  # analyzer_type
                    'v2',  # prompt_version (using improved game type detection)
                    result.get('confidence', 'medium')
                ))
                conn.commit()

            success_count += 1
        else:
            print(f"  FAILED: {raw_response}")
            fail_count += 1

        print()

    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {len(videos)}")


if __name__ == '__main__':
    process_all_videos()
